# <img src='story-512.png' card_color='#40DBB0' width='50' height='50' style='vertical-align:bottom'/> Fairy Tales
Stories and fairy tales by Hans Christian Andersen and the Brothers Grimm.

> **⚠️ This skill is no longer under active development.** It works, and
> will keep working, but new work is going into the
> [ovos-skill-common-tales](https://github.com/andlo/ovos-skill-common-tales)
> ecosystem instead - a proper orchestrator (similar in spirit to OCP for
> media skills) plus separate provider skills
> ([ovos-skill-andersen-tales](https://github.com/andlo/ovos-skill-andersen-tales),
> ovos-skill-grimm-tales, and more to come). That approach avoids the
> voice-command conflicts this skill runs into when installed alongside
> other storyteller skills, and is where new languages, sources, and
> features will land going forward. New installs should probably start
> there instead.

[![Tests](https://github.com/andlo/ovos-skill-fairytales/actions/workflows/test.yml/badge.svg)](https://github.com/andlo/ovos-skill-fairytales/actions/workflows/test.yml)
[![PyPI version](https://img.shields.io/pypi/v/ovos-skill-fairytales.svg)](https://pypi.org/project/ovos-skill-fairytales/)

## Install
```bash
pip install ovos-skill-fairytales
```

## About
This skill enables OVOS to tell a lot of H. C. Andersen's and the Brothers Grimm fairy tales. So make a cup of coco, and sit back and enjoy listning to the good clasic tales.

Content is from andersenstories.com and grimmstories.com, so please go visit there if you like the stories and want them in text to read.

https://www.andersenstories.com/
https://www.grimmstories.com/

This skill supports stories in the following languages: EN, DA, DE, ES, FR, IT, NL, PT, and uses the language your device is set up to use.

> **Note:** andersenstories.com only publishes in EN, DA, DE, ES, FR, IT, NL. Portuguese (PT) is Grimm-only - grimmstories.com has a Portuguese translation but andersenstories.com doesn't, so PT users will only hear Brothers Grimm stories, not H.C. Andersen ones.
>
> grimmstories.com actually offers several more languages (FI, HU, VI, TR, PL, RO, RU, UK, EL, ZH, JA, KO) that aren't included here yet, since they fall outside [OVOS's actively-tracked language set](https://openvoiceos.github.io/lang-support-tracker/). If you'd like your language added, please open an issue or a PR with translated `locale/<lang>/` files.

_“If you want your children to be intelligent, read them fairy tales. If you want them to be more intelligent, read them more fairy tales.”
Albert Einstein_

## Examples
* "Tell me a story about The little Mermaide"
* "Tell me the story about Cinderella "
* "Continue the story"

OVOS will then try to find the fairy tale if you told which one you wanted. If not, it will ask you.

## Credits
Andreas Lorensen (@andlo)

## Category
**Entertainment**


## Tags
#stories
#story
#tales
#fairy
#fairytale
#fairytales
#andersen
#hca
#grimm
