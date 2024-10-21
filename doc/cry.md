Oui, Jinja2 utilise la syntaxe `{{ param_name }}` pour afficher les variables dans les templates. En plus des expressions de variables, Jinja2 offre une riche série de blocs et de contrôles pour rendre les templates plus dynamiques et puissants.

Voici un aperçu des principales fonctionnalités et blocs conditionnels disponibles dans Jinja2 :

### 1. **Affichage de Variables**

- **Syntaxe :** `{{ variable_name }}`
  - Exemple : `{{ user.name }}`

### 2. **Structures Conditionnelles**

- **`if`** : Pour exécuter du code conditionnellement.
  - **Syntaxe :**
    ```jinja
    {% if condition %}
        ... code ...
    {% elif other_condition %}
        ... code ...
    {% else %}
        ... code ...
    {% endif %}
    ```
  - **Exemple :**
    ```jinja
    {% if user.is_active %}
        <p>Welcome, {{ user.name }}!</p>
    {% else %}
        <p>Please log in.</p>
    {% endif %}
    ```

### 3. **Boucles**

- **`for`** : Pour itérer sur des listes ou des dictionnaires.
  - **Syntaxe :**
    ```jinja
    {% for item in items %}
        ... code ...
    {% endfor %}
    ```
  - **Exemple :**
    ```jinja
    <ul>
    {% for user in users %}
        <li>{{ user.name }}</li>
    {% endfor %}
    </ul>
    ```

### 4. **Blocs et Extensions**

- **`block`** : Permet de définir des sections réutilisables dans les templates.
  - **Syntaxe :**
    ```jinja
    {% block block_name %}
        ... default content ...
    {% endblock %}
    ```
  - **Exemple dans un template de base :**
    ```jinja
    <html>
    <head>
        <title>{% block title %}Default Title{% endblock %}</title>
    </head>
    <body>
        {% block content %}{% endblock %}
    </body>
    </html>
    ```

- **`extends`** : Permet à un template d’hériter d'un autre.
  - **Syntaxe :**
    ```jinja
    {% extends "base.html" %}
    {% block content %}
        ... content ...
    {% endblock %}
    ```
  - **Exemple :**
    ```jinja
    {% extends "base.html" %}
    {% block content %}
        <p>This is a specific page content.</p>
    {% endblock %}
    ```

### 5. **Filtres**

- **Syntaxe :** `{{ value|filter_name }}`
  - **Exemple :**
    ```jinja
    {{ user.name|upper }}
    ```

### 6. **Macros**

- **`macro`** : Pour définir des blocs réutilisables ou des fonctions dans les templates.
  - **Syntaxe :**
    ```jinja
    {% macro input(name, value='', type='text') %}
        <input type="{{ type }}" name="{{ name }}" value="{{ value }}">
    {% endmacro %}
    ```

### 7. **Inclusion de Templates**

- **`include`** : Pour inclure des templates dans d'autres templates.
  - **Syntaxe :**
    ```jinja
    {% include 'header.html' %}
    ```

### 8. **Tests**

- **`test`** : Pour vérifier des conditions avec des tests intégrés.
  - **Exemple :**
    ```jinja
    {% if user.name is defined %}
        <p>User name is defined.</p>
    {% endif %}
    ```

Ces blocs et structures permettent de créer des templates dynamiques et modulaires tout en gardant le code bien organisé et réutilisable. Jinja2 est conçu pour être puissant mais accessible, avec une syntaxe qui est généralement facile à apprendre pour ceux qui sont familiers avec les langages de template ou les langages de programmation similaires.