.open userstudy.db
.mode csv
.separator ";"
select * from paired_choice inner join user_session on user_session.id = paired_choice.session_id;
.quit