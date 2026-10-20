-- Preserve existing 5-day rows until the explicitly authorized private QA reset.
-- Reusing the constraint name makes the atomic ALTER restartable before marking.
ALTER TABLE account_trials DROP CONSTRAINT account_trial_duration,
    ADD CONSTRAINT account_trial_duration CHECK (
        valid_until = DATE_ADD(valid_from, INTERVAL 259200 SECOND)
        OR valid_until = DATE_ADD(valid_from, INTERVAL 432000 SECOND)
    );
