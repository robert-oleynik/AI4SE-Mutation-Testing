# AI for Software Engineering

TODO

## Usage

> **Note:** The plugin needs to be reinstalled, if the plugin's source is changed.

Use the following commands, to install the plugin locally from source.

```sh
# Execute from project root
cd plugin
mvn clean install
```

After the plugin is installed, use the following commands to generate mutations for your project:

```sh
cd path/to/project
# or
cd example # inside of this repository
mvn de.hpi.ai4se.mutations:mutations-maven-plugin:0.0.1:generate
```

To use the shorthand `mutations:generate`, the following configurations `${maven.home}/conf/settings.xml` or `${user.home}/.m2/settings.xml`:

```xml
<pluginGroups>
	<pluginGroup>de.hpi.ai4se.mutations</pluginGroup>
</pluginGroups>
```

## Contents

TODO
