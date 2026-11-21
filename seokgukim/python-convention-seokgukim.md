# Python Conventions for seokgukim

These conventions apply to Python code written by seokgukim.

> Date: 2026-11-15  
> Author: seokgukim

## Overview

Use PascalCase for classes, snake_case for functions and ordinary identifiers, and SCREAMING_SNAKE_CASE for constants.
Use PEP 8-based formatting with 4-space indentation.
Use double quotes as the project default for strings.

## Naming

- Use PascalCase nouns for classes and suffix exception classes with Error.
- Use snake_case for modules, variables, parameters, and attributes.
- Use snake_case verbs or verb phrases for functions and methods.
- Keep constant names in SCREAMING_SNAKE_CASE.
- Prefix internal helpers and attributes with a single underscore.
- Include units in names when a value could be ambiguous.
- Preserve identifiers supplied by the standard library, external APIs, and exercise interfaces that must remain compatible.

```python
MAX_ITEM_COUNT = 100


class ItemCollection:
    def __init__(self):
        self._items = []

    def add_item(self, item):
        self._items.append(item)

    def count_items(self):
        return len(self._items)
```

## Formatting

- Use four spaces for indentation and no indentation tabs.
- Wrap long expressions inside parentheses, brackets, or braces instead of using backslash continuations.
- Put spaces around binary operators and after commas, and omit spaces immediately inside parentheses.
- Leave two blank lines around top-level functions and classes, and one blank line between methods.
- Group imports into standard-library, third-party, and local imports, separated by blank lines.
- Sort imports within each group and avoid wildcard imports.
- Use double quotes by default and f-strings for interpolation.

## Patterns

- Keep functions focused on one responsibility and prefer guard clauses over deeply nested conditionals.
- Use direct boolean checks for truthiness and is None or is not None when testing for a missing value.
- Use comprehensions for simple transformations and loops for logic with multiple steps or side effects.
- Avoid mutable default arguments and make mutation of caller-owned data explicit.
- Prefer small functions and introduce classes when state and behavior belong together.
- Prefer composition over deep inheritance and pass dependencies explicitly rather than relying on mutable globals.
- Extract shared helpers when repeated behavior has a clear common purpose.
- Separate core logic from input/output and avoid side effects during imports.
- Use context managers for resources that need cleanup and catch specific exceptions where recovery is possible.
- Add type hints when they clarify interfaces or nontrivial data structures.

## Vim and Neovim

Use the following command in the current Python buffer:

```vim
:setlocal shiftwidth=4 tabstop=4 softtabstop=4 expandtab
```

For persistent Python settings, add this Vimscript line to .vimrc or init.vim:

```vim
autocmd FileType python setlocal shiftwidth=4 tabstop=4 softtabstop=4 expandtab
```

shiftwidth controls indentation, tabstop controls the display width of tab characters, softtabstop controls editing behavior, and expandtab inserts spaces when pressing Tab.
The editor settings and source formatting must agree to keep indentation consistent.

## Comments and Documentation

- Explain purpose, ownership, assumptions, and return contracts when they are not clear from the code.
- Use triple double quotes for docstrings and begin with a short summary sentence.
- Use TODO comments to identify unfinished exercise work.
- Keep Markdown documentation ASCII-only.
- Keep each prose sentence on a single physical line without inserting a newline in the middle of the sentence.
- Use blank lines between paragraphs and allow code blocks to follow the formatting rules of their language.

## Scope

Naming and formatting changes should preserve program behavior.
Handle implementation fixes separately so that unfinished exercises remain easy to review.

## References

- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 257 - Docstring Conventions](https://peps.python.org/pep-0257/)
