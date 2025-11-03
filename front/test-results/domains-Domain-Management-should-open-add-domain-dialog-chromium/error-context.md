# Page snapshot

```yaml
- generic [ref=e5]:
  - generic [ref=e6]:
    - heading "SMTPy" [level=1] [ref=e8]
    - heading "Connexion" [level=2] [ref=e9]
    - paragraph [ref=e10]: Connectez-vous à votre compte
  - generic [ref=e14]:
    - generic [ref=e15]:
      - generic [ref=e16]: Nom d'utilisateur ou email *
      - generic [ref=e17]:
        - generic: 
        - textbox "Nom d'utilisateur ou email *" [ref=e18]:
          - /placeholder: Entrez votre nom d'utilisateur
          - text: admin
    - generic [ref=e19]:
      - generic [ref=e20]: Mot de passe *
      - generic [ref=e21]:
        - generic: 
        - generic [ref=e22]:
          - textbox "Entrez votre mot de passe" [ref=e23]: password
          - img [ref=e24]
    - generic [ref=e26]:
      - checkbox [ref=e29] [cursor=pointer]
      - link "Mot de passe oublié?" [ref=e31] [cursor=pointer]:
        - /url: /auth/forgot-password
    - button "Se connecter" [disabled] [ref=e33]:
      - img [ref=e34]
      - generic [ref=e37]: Se connecter
    - generic [ref=e39]: ou
    - paragraph [ref=e41]:
      - text: Vous n'avez pas de compte?
      - link "Créer un compte" [ref=e42] [cursor=pointer]:
        - /url: /auth/register
  - link " Retour à l'accueil" [ref=e44] [cursor=pointer]:
    - /url: /
    - generic [ref=e45]: 
    - text: Retour à l'accueil
```