# claims/ — advisory locks for parallel writers

Before working a scope, drop `<scope>.claim.json` here (see ../CONCURRENCY.md rule 2).
A fresh claim (age < ttl_min) means another writer owns that scope — pick another.
Delete your claim when done. These are git-carried advisory locks, not hard locks.
