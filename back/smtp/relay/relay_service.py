"""
Async SMTP Relay Service for SMTPy

This service handles outbound email forwarding with:
- Async SMTP connections (aiosmtplib)
- Connection pooling
- Retry logic with exponential backoff
- Queue management
- Rate limiting
- Error handling and logging
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.message import EmailMessage
from enum import Enum
from typing import List, Optional, Dict
from collections import deque

import aiosmtplib
from aiosmtplib import SMTPException

from shared.core.config import SETTINGS

logger = logging.getLogger(__name__)


class EmailPriority(Enum):
    """Email priority levels for queue management"""
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class EmailJob:
    """Represents an email forwarding job"""
    message: EmailMessage
    targets: List[str]
    mail_from: str
    priority: EmailPriority = EmailPriority.NORMAL
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def __lt__(self, other):
        """For priority queue ordering"""
        return self.priority.value < other.priority.value


class SMTPRelayService:
    """
    Async SMTP relay service with connection pooling and retry logic.

    Features:
    - Connection pooling for better performance
    - Exponential backoff retry logic
    - Rate limiting to prevent overwhelming relay servers
    - Queue management with priority support
    - Comprehensive error handling and logging
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        username: str = None,
        password: str = None,
        use_tls: bool = True,
        pool_size: int = 5,
        max_queue_size: int = 1000,
        rate_limit: int = 100,  # emails per minute
    ):
        """
        Initialize SMTP relay service.

        Args:
            host: SMTP server hostname
            port: SMTP server port
            username: SMTP username for authentication
            password: SMTP password for authentication
            use_tls: Use STARTTLS for secure connection
            pool_size: Number of SMTP connections to maintain
            max_queue_size: Maximum number of emails in queue
            rate_limit: Maximum emails per minute
        """
        self.host = host or SETTINGS.SMTP_HOST
        self.port = port or SETTINGS.SMTP_PORT
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.pool_size = pool_size
        self.max_queue_size = max_queue_size
        self.rate_limit = rate_limit

        # Connection pool
        self._connection_pool: asyncio.Queue = asyncio.Queue(maxsize=pool_size)
        self._pool_initialized = False

        # Email queue
        self._email_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)

        # Rate limiting
        self._sent_timestamps: deque = deque(maxlen=rate_limit)
        self._rate_limit_lock = asyncio.Lock()

        # Statistics
        self.stats = {
            "sent": 0,
            "failed": 0,
            "retried": 0,
            "queued": 0
        }

        # Worker tasks
        self._workers: List[asyncio.Task] = []
        self._running = False

        logger.info(
            f"SMTPRelayService initialized: {self.host}:{self.port} "
            f"(pool_size={pool_size}, rate_limit={rate_limit}/min)"
        )

    async def _create_connection(self) -> aiosmtplib.SMTP:
        """Create a new SMTP connection"""
        try:
            smtp = aiosmtplib.SMTP(
                hostname=self.host,
                port=self.port,
                timeout=30,
                use_tls=False  # We'll use STARTTLS manually
            )

            await smtp.connect()
            logger.debug(f"Connected to SMTP server {self.host}:{self.port}")

            # Use STARTTLS if enabled
            if self.use_tls:
                await smtp.starttls()
                logger.debug("STARTTLS established")

            # Authenticate if credentials provided
            if self.username and self.password:
                await smtp.login(self.username, self.password)
                logger.debug(f"Authenticated as {self.username}")

            return smtp

        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            raise

    async def _initialize_pool(self):
        """Initialize the connection pool"""
        if self._pool_initialized:
            return

        logger.info(f"Initializing SMTP connection pool ({self.pool_size} connections)...")

        for i in range(self.pool_size):
            try:
                conn = await self._create_connection()
                await self._connection_pool.put(conn)
                logger.debug(f"Connection {i+1}/{self.pool_size} added to pool")
            except Exception as e:
                logger.error(f"Failed to initialize connection {i+1}: {e}")

        self._pool_initialized = True
        logger.info("Connection pool initialized")

    async def _get_connection(self) -> aiosmtplib.SMTP:
        """Get a connection from the pool"""
        try:
            conn = await asyncio.wait_for(
                self._connection_pool.get(),
                timeout=30
            )

            # Check if connection is still alive
            try:
                await conn.noop()
                return conn
            except Exception:
                # Connection dead, create new one
                logger.warning("Dead connection detected, creating new one")
                return await self._create_connection()

        except asyncio.TimeoutError:
            logger.warning("Connection pool exhausted, creating temporary connection")
            return await self._create_connection()

    async def _return_connection(self, conn: aiosmtplib.SMTP):
        """Return a connection to the pool"""
        try:
            if not self._connection_pool.full():
                await self._connection_pool.put(conn)
            else:
                # Pool is full, close this connection
                await conn.quit()
        except Exception as e:
            logger.error(f"Error returning connection to pool: {e}")
            try:
                await conn.quit()
            except:
                pass

    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        async with self._rate_limit_lock:
            now = datetime.utcnow()

            # Remove timestamps older than 1 minute
            while self._sent_timestamps and (now - self._sent_timestamps[0]) > timedelta(minutes=1):
                self._sent_timestamps.popleft()

            # Check if we've hit the rate limit
            if len(self._sent_timestamps) >= self.rate_limit:
                # Calculate wait time
                oldest = self._sent_timestamps[0]
                wait_time = 60 - (now - oldest).total_seconds()
                if wait_time > 0:
                    logger.warning(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)

            # Record this send
            self._sent_timestamps.append(now)

    async def _send_email(
        self,
        message: EmailMessage,
        targets: List[str],
        mail_from: str
    ) -> bool:
        """
        Send email through SMTP relay.

        Returns:
            True if successful, False otherwise
        """
        conn = None
        try:
            # Check rate limit
            await self._check_rate_limit()

            # Get connection from pool
            conn = await self._get_connection()

            # Send the email
            await conn.sendmail(
                mail_from,
                targets,
                message.as_string()
            )

            logger.info(f"Successfully sent email to {len(targets)} recipient(s)")
            self.stats["sent"] += 1
            return True

        except SMTPException as e:
            logger.error(f"SMTP error sending email: {e}")
            self.stats["failed"] += 1
            return False

        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            self.stats["failed"] += 1
            return False

        finally:
            if conn:
                await self._return_connection(conn)

    async def _process_job(self, job: EmailJob) -> bool:
        """
        Process an email job with retry logic.

        Returns:
            True if successful, False otherwise
        """
        try:
            success = await self._send_email(
                job.message,
                job.targets,
                job.mail_from
            )

            if success:
                return True

            # Failed, check if we should retry
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                self.stats["retried"] += 1

                # Exponential backoff: 2^retry_count seconds
                wait_time = 2 ** job.retry_count
                logger.info(
                    f"Retrying email (attempt {job.retry_count}/{job.max_retries}) "
                    f"in {wait_time}s"
                )

                await asyncio.sleep(wait_time)

                # Re-queue the job
                await self._email_queue.put(job)
                return False
            else:
                logger.error(
                    f"Email failed after {job.max_retries} retries, giving up"
                )
                return False

        except Exception as e:
            logger.error(f"Error processing job: {e}")
            return False

    async def _worker(self, worker_id: int):
        """Worker task that processes emails from the queue"""
        logger.info(f"Worker {worker_id} started")

        while self._running:
            try:
                # Get job from queue with timeout
                job = await asyncio.wait_for(
                    self._email_queue.get(),
                    timeout=1.0
                )

                logger.debug(f"Worker {worker_id} processing job")
                await self._process_job(job)
                self._email_queue.task_done()

            except asyncio.TimeoutError:
                # No jobs in queue, continue waiting
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)

        logger.info(f"Worker {worker_id} stopped")

    async def start(self, num_workers: int = 3):
        """Start the relay service with worker tasks"""
        if self._running:
            logger.warning("Relay service already running")
            return

        logger.info(f"Starting relay service with {num_workers} workers...")

        # Initialize connection pool
        await self._initialize_pool()

        # Start workers
        self._running = True
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)

        logger.info("Relay service started successfully")

    async def stop(self):
        """Stop the relay service gracefully"""
        logger.info("Stopping relay service...")

        self._running = False

        # Wait for queue to be processed
        if not self._email_queue.empty():
            logger.info(f"Waiting for {self._email_queue.qsize()} queued emails to be sent...")
            await self._email_queue.join()

        # Cancel workers
        for worker in self._workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

        # Close all connections in pool
        while not self._connection_pool.empty():
            try:
                conn = await self._connection_pool.get()
                await conn.quit()
            except:
                pass

        logger.info("Relay service stopped")

    async def send(
        self,
        message: EmailMessage,
        targets: List[str],
        mail_from: str = "noreply@smtpy.fr",
        priority: EmailPriority = EmailPriority.NORMAL
    ) -> bool:
        """
        Queue an email for sending.

        Args:
            message: Email message to send
            targets: List of recipient email addresses
            mail_from: Sender email address
            priority: Email priority level

        Returns:
            True if queued successfully, False if queue is full
        """
        if not self._running:
            logger.error("Cannot send email: relay service not running")
            return False

        if self._email_queue.full():
            logger.error(f"Email queue full ({self.max_queue_size}), cannot queue email")
            return False

        job = EmailJob(
            message=message,
            targets=targets,
            mail_from=mail_from,
            priority=priority
        )

        try:
            await self._email_queue.put(job)
            self.stats["queued"] += 1
            logger.debug(f"Email queued for {len(targets)} recipient(s)")
            return True
        except Exception as e:
            logger.error(f"Failed to queue email: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get relay service statistics"""
        return {
            **self.stats,
            "queue_size": self._email_queue.qsize(),
            "pool_size": self._connection_pool.qsize(),
            "running": self._running
        }


# Global relay service instance
_relay_service: Optional[SMTPRelayService] = None


async def get_relay_service() -> SMTPRelayService:
    """Get or create the global relay service instance"""
    global _relay_service

    if _relay_service is None:
        _relay_service = SMTPRelayService(
            username=getattr(SETTINGS, 'SMTP_USER', None),
            password=getattr(SETTINGS, 'SMTP_PASSWORD', None),
        )
        await _relay_service.start()

    return _relay_service


async def send_email(
    message: EmailMessage,
    targets: List[str],
    mail_from: str = "noreply@smtpy.fr",
    priority: EmailPriority = EmailPriority.NORMAL
) -> bool:
    """
    Convenience function to send email through the relay service.

    Args:
        message: Email message to send
        targets: List of recipient email addresses
        mail_from: Sender email address
        priority: Email priority level

    Returns:
        True if queued successfully, False otherwise
    """
    relay = await get_relay_service()
    return await relay.send(message, targets, mail_from, priority)
