Audit ontology and table consistency across the repository.

Goal
----

Detect logical inconsistencies in ontology tables and mappings.

Focus especially on relationships among:

- scripts
- languages
- Unicode blocks
- specimen samples
- Polyglossia mappings
- language profiles

Do NOT modify code.
Report findings only.


Scope
-----

fontshow/ontology/
fontshow/language_tables.py
fontshow/unicode_tables.py
fontshow/specimen/
tests/


Checks
------

1. Script Table Integrity

Verify that each script defined in the ontology:

- appears consistently across all relevant tables
- has required properties (name, sample, mapping, etc.)

Detect scripts that:

- exist in one table but not another
- lack specimen definitions
- lack language associations.


2. Language Mapping Consistency

Check mappings between:

- LANGUAGE_PROFILES
- SCRIPT_TO_POLYGLOSSIA
- language tables

Detect:

- languages referencing undefined scripts
- scripts referenced by no language
- inconsistent naming conventions.


3. Unicode Block Coverage

Verify that Unicode blocks referenced in tables:

- exist in Unicode standards
- correspond to the expected script.

Detect mismatches such as:

- block assigned to wrong script
- duplicated block definitions
- blocks referenced but not defined.


4. Specimen Coverage

Verify that each script used by the system has:

- at least one specimen sample
- a valid fallback mechanism.

Detect:

- scripts without specimen definitions
- specimen strings incompatible with the script.


5. Duplicate Definitions

Detect duplicated entries such as:

- identical script definitions in multiple tables
- repeated language entries
- redundant Unicode block assignments.


6. Naming Consistency

Verify that naming conventions match across tables.

Examples:

- script identifiers use consistent case
- language identifiers follow a uniform format
- table keys match expected canonical names.


7. Test Coverage

Verify that ontology tables are exercised by tests.

Detect:

- tables defined but never referenced in tests
- ontology invariants not tested.


Output
------

Report findings grouped by category:

- missing script definitions
- inconsistent language mappings
- Unicode block mismatches
- missing specimens
- duplicated entries
- naming inconsistencies
- untested ontology tables

For each finding include:

- file path
- table or variable name
- explanation of the inconsistency.


Constraints
-----------

- Do not invent ontology entries.
- Do not modify code.
- Focus only on logical consistency across tables.
