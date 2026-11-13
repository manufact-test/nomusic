-- Additive separation of existing email conversations and song reports.
-- Existing tickets remain general and retain all messages and delivery state.
ALTER TABLE support_tickets
 ADD COLUMN kind VARCHAR(16) NOT NULL DEFAULT 'general',
 ADD COLUMN report_json TEXT NULL,
 ADD COLUMN report_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL,
 ADD KEY support_kind_account(user_id,kind,status,id),
 ADD KEY support_report_duplicate(user_id,report_hash,status);
ALTER TABLE support_messages ADD COLUMN mail_required TINYINT UNSIGNED NOT NULL DEFAULT 1;
ALTER TABLE track_requests ADD KEY track_request_song_queue(service,service_track_id,status,id);
