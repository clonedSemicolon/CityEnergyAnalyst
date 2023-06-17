"""
A base class for creating CEA plugins. Subclass this class in your own namespace to become a CEA plugin.
"""




import importlib
import os
import configparser
from typing import Generator, Sequence
import yaml
import inspect
import cea.schemas
import cea.config
import cea.plots.categories
import cea.inputlocator
import warnings
from cea.utilities import identifier

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class CeaPlugin(object):
    """
    A CEA Plugin defines a list of scripts and a list of plots - the CEA uses this to populate the GUI
    and other interfaces. In addition, any input- and output files need to be defined.
    """

    @property
    def scripts(self):
        """Return the scripts.yml dictionary."""
        scripts_yml = os.path.join(os.path.dirname(inspect.getmodule(self).__file__), "scripts.yml")
        if not os.path.exists(scripts_yml):
            return {}
        with open(scripts_yml, "r") as scripts_yml_fp:
            scripts = yaml.safe_load(scripts_yml_fp)
        return scripts

    @property
    def plot_categories(self):
        """
        Return a list of :py:class`cea.plots.PlotCategory` instances to add to the GUI. The default implementation
        uses the ``plots.yml`` file to create PluginPlotCategory instances that use PluginPlotBase to provide a
        simplified plot mechanism using cufflinks_

        .. _cufflinks: https://plotly.com/python/cufflinks/
        """
        plots_yml = os.path.join(os.path.dirname(inspect.getmodule(self).__file__), "plots.yml")
        if not os.path.exists(plots_yml):
            return {}
        with open(plots_yml, "r") as plots_yml_fp:
            categories = yaml.load(plots_yml_fp, Loader=yaml.CLoader)
        return [PluginPlotCategory(category_label, categories[category_label], self) for category_label in categories.keys()]

    @property
    def schemas(self):
        """Return the schemas dict for this plugin - it should be in the same format as ``cea/schemas.yml``

        (You don't actually have to implement this for your own plugins - having a ``schemas.yml`` file in the same
        folder as the plugin class will trigger the default behavior)
        """
        schemas_yml = os.path.join(os.path.dirname(inspect.getmodule(self).__file__), "schemas.yml")
        if not os.path.exists(schemas_yml):
            return {}
        with open(schemas_yml, "r") as schemas_yml_fp:
            schemas = yaml.load(schemas_yml_fp, Loader=yaml.CLoader)
        return schemas

    @property
    def config(self):
        """
        Return the configuration for this plugin - the `cea.config.Configuration` object will include these.

        The format is expected to be the same format as `default.config` in the CEA.

        :rtype: configparser.ConfigParser
        """

        plugin_config = os.path.join(os.path.dirname(inspect.getmodule(self).__file__), "plugin.config")
        parser = configparser.ConfigParser()
        if not os.path.exists(plugin_config):
            return parser
        parser.read(plugin_config)
        return parser

    def __str__(self):
        """To enable encoding in cea.config.PluginListParameter, return the fqname of the class"""
        return "{module}.{name}".format(module=self.__class__.__module__, name=self.__class__.__name__)




if __name__ == "__main__":
    # try to plot the first plugin found
    # FIXME: remove this before commit
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    plugin = config.plugins[0]
    category = list(plugin.plot_categories)[0]
    plot_class = list(category.plots)[0]

    print(plot_class.expected_parameters)
    print(plot_class.name)
    print(plot_class.category_path)

    plot = plot_class(config.project, {"scenario-name": config.scenario_name}, cache)
    print(plot.category_path)
    print(plot.plot(auto_open=True))


def instantiate_plugin(plugin_fqname):
    """Return a new CeaPlugin based on it's fully qualified name - this is how the config object creates plugins"""
    try:
        plugin_path = plugin_fqname.split(".")
        plugin_module = ".".join(plugin_path[:-1])
        plugin_class = plugin_path[-1]
        module = importlib.import_module(plugin_module)
        instance = getattr(module, plugin_class)()
        return instance
    except BaseException as ex:
        warnings.warn(f"Could not instantiate plugin {plugin_fqname} ({ex})")
        return None


def add_plugins(default_config, user_config):
    """
    Patch in the plugin configurations during __init__ and __setstate__

    :param configparser.ConfigParser default_config:
    :param configparser.ConfigParser user_config:
    :return: (modifies default_config and user_config in-place)
    :rtype: None
    """
    plugin_fqnames = cea.config.parse_string_to_list(user_config.get("general", "plugins"))
    for plugin in [instantiate_plugin(plugin_fqname) for plugin_fqname in plugin_fqnames]:
        if plugin is None:
            # plugin could not be instantiated
            continue
        for section_name in plugin.config.sections():
            if section_name in default_config.sections():
                raise ValueError("Plugin tried to redefine config section {section_name}".format(
                    section_name=section_name))
            default_config.add_section(section_name)
            if not user_config.has_section(section_name):
                user_config.add_section(section_name)
            for option_name in plugin.config.options(section_name):
                if option_name in default_config.options(section_name):
                    raise ValueError("Plugin tried to redefine parameter {section_name}:{option_name}".format(
                        section_name=section_name, option_name=option_name))
                default_config.set(section_name, option_name, plugin.config.get(section_name, option_name))
                if "." not in option_name and not user_config.has_option(section_name, option_name):
                    user_config.set(section_name, option_name, default_config.get(section_name, option_name))