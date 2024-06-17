# Ideas for Mutation Generators

- [x] Replace e.g. a condition, call parameter or similars with the `<infilling>` tag and query the AI for the missing bits.
- [x] Strip everything except function signature and doc comments. Use the LLM to generate the misisng bits.
- [x] Select a token of the input function and force the AI to generate a different approach starting from this token. Further points of exploration:
- [x] Beam Search
- [x] Comment out old code and prompt for new code

# Technical Features

- [ ] Pass decorators into MutationTargets
- [ ] Provide function context (e. g. class around method)
- [ ] Provide more context to avoid loops
- [x] Use version 1.1 2b of model
- [ ] Use 7b model

# Against which baseline to evaluate?

- [x] Mutatest
- [-] Custom Mutation testing tool.

# What Metrics to use for Evaluation?

- [ ] Number of disjoint/uncaught mutants (per project)?

# What Projects to use for testing?

- [ ] Flask
- [ ] ?

# Finetuning

- [ ] Mine real changes (check for simultaneous changes of code and test)
- [ ] Synthetic test data based on mutatest
- [ ] Fine tune once per generator (regarding specific format)
