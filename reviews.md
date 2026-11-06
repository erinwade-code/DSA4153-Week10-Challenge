#Review 1: Member 1 -> Member2
Reviewer: Member 1 (Acuna)
Author: Member 2 (Jacinto)
Reviewed commit: bad8bccb7898b644a58750aadba78959ff786751
Feedback:
- readers work as intended
- no problems found on my end
Outcome: Approved

#Review 4: Member 4 -> Member 5
Reviewer: Member 4 (Amon)
Author: Member 5 (Dolar)
Reviewed commit: c4c81a9a78f84e9c10d3e13be8b31e9ea9e321e5
Files reviewed: src/export_staging.py (53c2e41), tests/test_export_staging.py (4b8e07a)
Feedback:
- Staging folder and cleanup work as intended.
- verify_roundtrip_exports only compares lifeExp and gdpPercap, so changing country, continent, year or pop in an export still returns True.
- A blank lifeExp value also passes.
- The unit test only corrupts lifeExp, which is already checked, so it can't catch the problem above. It should also change country or pop.
Author response: Empty For Now
Outcome: Changes requested (PR #5), <update to Approved after the fix, with the fix commit hash>
