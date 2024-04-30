package de.hpi.ai4se.mutations;

import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.stream.Collectors;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import org.apache.maven.plugin.AbstractMojo;
import org.apache.maven.plugin.MojoExecutionException;
import org.apache.maven.plugin.MojoFailureException;
import org.apache.maven.plugins.annotations.LifecyclePhase;
import org.apache.maven.plugins.annotations.Mojo;
import org.apache.maven.plugins.annotations.Parameter;
import org.apache.maven.project.MavenProject;

@Mojo(name = "generate", defaultPhase = LifecyclePhase.GENERATE_SOURCES)
public class GenerateMojo extends AbstractMojo {
	@Parameter(property = "project", required = true, readonly = true)
	protected MavenProject project;

	@Parameter(defaultValue = "${project.compileSourceRoots}", readonly = false, required = true)
	private List<String> compileSourceRoots;

	@Parameter(defaultValue = "${project.build.directory}/generated-soruces/mutations", readonly = false, required = true)
	private File generatedSourcesDir;

	@Parameter(property = "maven.compiler.outputDirectory", defaultValue = "${project.build.outputDirectory}", required = true, readonly = false)
	private File outputDirectory;

	@Override
	public void execute() throws MojoExecutionException, MojoFailureException {
		Path generatedSourcesDir = Paths.get(this.generatedSourcesDir.getPath());
		if (!Files.exists(generatedSourcesDir)) {
			try {
				Files.createDirectories(generatedSourcesDir);
			} catch (IOException e) {
				throw new MojoFailureException("failed to create generated sources dir: " + e.getMessage());
			}
		}
		if (!Files.isDirectory(Paths.get(this.generatedSourcesDir.getPath()))) {
			throw new MojoFailureException("`" + this.generatedSourcesDir + "` is not a directory");
		}

		JavaFileScanner scanner = new JavaFileScanner();
		for (String sourceRoot: compileSourceRoots) {
			try {
				scanner.scanRoot(Paths.get(sourceRoot));;
			} catch(IOException e) {
				throw new MojoFailureException("failed to scan for source files: " + e.getMessage());
			}
		}
		List<SourceMutation> mutations = scanner.getSources()
			.stream()
			.filter((Source source) -> {
				try {
					source.identifyMutations();
				} catch (IOException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
				// TODO: Ignore non-mutated files
				return true;
			})
			.flatMap(SourceMutation::generate)
			.collect(Collectors.toList());
		getLog().info("Generated Source Files: " + mutations.size());

		getLog().debug("Generated Sources:");
		for (SourceMutation mutation: mutations) {
			Path rel = mutation.getOrigin().getSourceFile().getParent();
			Path dir = generatedSourcesDir.resolve(rel);
			if (!Files.exists(dir)) {
				try {
					Files.createDirectories(dir);
				} catch (IOException e) {
					throw new MojoFailureException("failed to create generate source directory: " + e.getMessage());
				}
			}
			Path file = dir.resolve(mutation.getName() + ".java");
			try {
				// TODO: Handle Charset
				Files.writeString(file, mutation.getMutatedSource());
			} catch (IOException e) {
				throw new MojoFailureException("failed to write generate sources: " + e.getMessage());
			}
			getLog().debug(file.toString());
		}
	}
}
