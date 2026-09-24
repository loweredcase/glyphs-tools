# Plugin Manager submission

The collection can remain a set of ordinary `.py` scripts. It does **not** need to become a Glyphs plug-in bundle.

The official Plugin Manager index is:

`schriftgestalt/glyphs-packages`

Add an entry to the `scripts = (...)` section of `packages.plist` and submit a pull request. A proposed entry for this repository is:

```
{
    descriptions = {
        en = "Addition Projects’ collection of modular drawing and font-production tools for Glyphs 4.";
    };
    installName = "Addition Projects";
    titles = {
        en = "Addition Projects Glyphs Tools";
    };
    url = "https://github.com/loweredcase/glyphs-tools";
    minGlyphsVersion = "4.0";
    dependencies = (vanilla);
},
```

Before submitting:

1. Confirm all scripts run in a current Glyphs 4 build.
2. Push the Glyphs 4 version to the repository’s default branch.
3. Confirm the README and license are public.
4. Fork `schriftgestalt/glyphs-packages`, add the entry, and run its package validator.
5. Submit the pull request.

The Glyphs team also accepts questions/submission help through the Glyphs Forum or by email, but a package-index pull request is the documented direct route.
