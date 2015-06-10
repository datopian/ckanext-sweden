## Creating a combined translation file

You should be able to run make on it's own, but you can specify the path
to the src directory containing ckan and it's extensions

```
make SOURCESDIR=/path/to/sources

```
you can edit the the PLUGINS line to update the list of plugins that need
their translations pulled

After this has been run, the i18n directory in THIS directory will contain
the combined translations

The i18n directory in the root directory should just contain translations
for ckanext-sweden alone

## Make Ckan load custom translations
 
This can be done by setting the ``ckan.i18n_directory`` configuration
option (in the ``[app:main]`` section of ckan configuration file)
to point to the root directory of  this repository (or any directory
containing a copy of the ``i18n`` folder, for what matters).
