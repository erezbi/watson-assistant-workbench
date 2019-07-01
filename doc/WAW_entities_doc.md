## Entities
Values of each entity are specified in a separate file with the name corresponding to the entity name
e.g. `first_name.csv`
There is one entity value per row of the file. The value can be followed by its synonyms separated by semicolumns

**Example:**
```
amy
john;johny;johnny;ian
susanne;susan
```
**Recommendation:** Entities files are typically placed to a separate directory `<app_root>/entities` or directories.

### Patterns
For pattern entities the pattern should be prefixed by `~`

**Example:**
```
~email;\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b
~fullUSphone;(\d{3})-(\d{3})-(\d{4})
```

# Contextual Entities

Contextual entities are annotated on intent examples using XML tags. More than one entity can be annotated in one example.

**Example:**
```
I'd like <color>red</color> dress
i like <color>blue</color> and <color>green</color>
```

Annotations cannot be nested and only the most inner ones are taken into account. Validations is provided for matching tags. When there are invalid annotation the script exits with error. The functionality is covered by `intents_csv2json.py` script. Currently only one way conversion is provided (CSV -> JSON).

### Naming conventions

**Only english letters, numbers, hyphens and underscores are allowed in entities names.**

You are supposed not to use entities names starting with `sys-` as Conversation tool offers some system entities with this prefix.

_Following are only recommendations, intent name has no impact on the behavior of the conversation._

- The entity name should be lower-cased
- There shouldn't be any domain prefix as entity is usually cross-domain (e.g. color)

**Example:**`first_name`

# Fuzzy matching
For now, only global fuzzy matching (for all entities) is supported. To turn it on, add `fuzzy` setting to the `entities` section of your config file. The value can be one of `on`, `On`, `true` or `True`. E.g.:
```ini
[entities]
fuzzy = On
```