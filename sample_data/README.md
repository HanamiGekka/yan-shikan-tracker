# Synthetic sample data

All files in sample_data are synthetic. They do not contain or derive from real user records.

The three future-dated workbooks use the same sheet name and columns as the private daily Excel files. They support demos, regression tests, and schema inspection. `赶路` is an intentionally historical category alias. The sample CSV demonstrates category configuration.

For CLI experiments, place these workbooks only in a temporary test data root using the test setup in the main README. Never place demo records in your real `data/` directory.

Real user `data/` and `output/` stay local only and are never Git candidates.
