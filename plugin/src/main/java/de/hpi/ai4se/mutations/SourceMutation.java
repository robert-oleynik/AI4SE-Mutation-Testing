package de.hpi.ai4se.mutations;

import java.util.stream.Stream;

import lombok.Getter;

public class SourceMutation {
	/**
	 * @brief Path to original/non-mutated file.
	 */
	@Getter
	private Source origin;

	/**
	 * @brief Name of the mutation.
	 */
	@Getter
	private String name;

	/**
	 * @brief Mutated source code.
	 */
	@Getter
	private String mutatedSource;

	public static Stream<SourceMutation> generate(Source source) {
		// TODO: Generate multiple mutations.
		return Stream.empty();
	}
}
