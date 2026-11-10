"""Black-box unit tests for create_recipe_slug (KacperS), cases KS-01 .. KS-10."""

import re

import pytest

from mealie.schema.recipe.recipe import create_recipe_slug

# A URL-safe slug: lowercase letters/digits separated by single hyphens, no hyphen at either end
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


@pytest.mark.parametrize(
    "name, expected",
    [
        pytest.param("Pasta Fagioli", "pasta-fagioli", id="KS-01-ordinary-name"),
        pytest.param("SPAGHETTI Carbonara", "spaghetti-carbonara", id="KS-02-uppercase"),
        pytest.param("  Pasta    Fagioli  ", "pasta-fagioli", id="KS-03-extra-whitespace"),
        pytest.param("Żurek łódzki z jajkiem", "zurek-lodzki-z-jajkiem", id="KS-04-polish-characters"),
        pytest.param("Chili!!! @ Home #1", "chili-home-1", id="KS-05-special-characters"),
    ],
)
def test_create_recipe_slug_valid_names(name: str, expected: str):
    slug = create_recipe_slug(name)

    assert slug == expected
    assert SLUG_PATTERN.match(slug)


@pytest.mark.parametrize(
    "name, max_length",
    [
        pytest.param("a" * 300, 250, id="KS-06-longer-than-default-max-length"),
        pytest.param("Spaghetti Carbonara z boczkiem", 10, id="KS-07-custom-max-length"),
    ],
)
def test_create_recipe_slug_is_truncated(name: str, max_length: int):
    slug = create_recipe_slug(name, max_length=max_length)

    assert 0 < len(slug) <= max_length
    # truncation must not leave a dangling hyphen and must keep the start of the full slug
    assert SLUG_PATTERN.match(slug)
    assert create_recipe_slug(name, max_length=10_000).startswith(slug)


def test_create_recipe_slug_exactly_max_length_is_not_truncated():
    """KS-08: a name whose slug has exactly `max_length` characters stays unchanged."""
    name = "b" * 250

    assert create_recipe_slug(name) == name


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("", id="KS-09-empty-name"),
        pytest.param("!!! ??? ###", id="KS-10-only-special-characters"),
    ],
)
def test_create_recipe_slug_invalid_name_raises_value_error(name: str):
    with pytest.raises(ValueError):
        create_recipe_slug(name)
