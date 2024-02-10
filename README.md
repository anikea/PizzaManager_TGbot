Bot can add, remove, edit products inside.
req modules python3 in reqs.txt
.env file with token and db like:

----
TOKEN=your_token
DB_LITE=sqlite+aiosqlite:///MyBot///your_name.db
----

First of all u need create a group and add bot in, after change status of all users u need to admin and type /admin in chat, message should dissappear.

Then, all users who have status "admin" can write /admin in private messages to bot and got all persmissions.
