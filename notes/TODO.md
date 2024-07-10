# Ideas for Mutation Generators

- [x] Replace e.g. a condition, call parameter or similars with the `<infilling>` tag and query the AI for the missing bits.
- [x] Strip everything except function signature and doc comments. Use the LLM to generate the misisng bits.
- [x] Select a token of the input function and force the AI to generate a different approach starting from this token. Further points of exploration:
- [x] Beam Search
- [x] Comment out old code and prompt for new code

# Technical Features

- [ ] Pass decorators into MutationTargets
- [x] Provide function context (e. g. class around method)
- [x] Provide more context to avoid loops
- [x] Use version 1.1 2b of model
- [x] Use 7b model

# Against which baseline to evaluate?

- [x] Mutatest
- [-] Custom Mutation testing tool.

# What Projects to use for testing?

- [ ] Flask
- [ ] ?

# Finetuning

- [x] Mine real changes (check for simultaneous changes of code and test)
- [ ] Synthetic test data based on mutatest
- [x] Fine tune once per generator (regarding specific format)

# Report

- Measure number of syntax errors, caught mutations, missed mutations and timeouts
  - Per generator
  - Per model + fine-tuned models
  - Against traditional mutation testers
- Measure performance against traditional mutation testers
- "Human-likeness" (manually evaluate)
- Related Work / Intro: andere paper zitieren als "Inspiration"
  - müssen nicht unbedingt viele paper lesen und zitieren
