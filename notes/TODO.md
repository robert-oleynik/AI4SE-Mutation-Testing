# Ideas for Mutation Generators

- [ ] Replace e.g. a condition, call parameter or similars with the `<infilling>` tag and query the AI for the missing bits.
- [ ] Strip everything except function signature and doc comments. Use the LLM to generate the misisng bits.
- [ ] Select a token of the input function and force the AI to generate a different approach starting from this token. Further points of exploration:
	- e.g. Beam Search

# Against which baseline to evaluate?

- [ ] Mutatest
- [ ] Custom Mutation testing tool.

# What Metrics to use for Evaluation?

- [ ] Number of disjoint/uncaught mutants (per project)?

# What Projects to use for testing?

- [ ] Flask
- [ ] ?

