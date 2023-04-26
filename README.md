# MissingSemesterBot

## Using the bot
The bot runs on our testing discord server but can actually be used on any discord server.
Using the newish slash-commands discord implemented the bot can just be invoked with /message_times /wordcloud and /lovescore followed by the user(s)
While the bot is running it will regularly fetch messages in the background, so the result will change until the bot cached all the messages on the server, this is done so wordclouds can be generated over the full message history while not breaking anything by trying to fetch 4 years of message history from the server at once.

## Learnings
* Discord partnered with Git to do automatic secret scanning if one leaks their bot token
* An API should have a timeline which things changed when and tutorials should always be clearly timestamped to be able to easily see if what you are trying to implement is outdated
* Caching data and saving it locally might work better in a database format or some other pre-defined format instead of creating your own format and working with that
* For slower commands one needs to delay the bot response else the bot request times out
* For different tasks different dummy data can work: Lorem Ipsum works to test formatting but would be rather ill fitted for our purposes of testing the commands. Just copy pasting the entire bee movie script into discord is more akin to natural english conversation (minus the fact that "Barry" is one of our most used words and our conversation is very honey focused)
* Its not trivial to calculate the average or difference of hours if they are independed of days, i.e. when 23:00-1:00 is 2hours and 1:00-23:00 is also -2hours
* Just like all lovescore calculations one can find on the internet its always important to use some weird number crunching to calculate such a score instead of actual metrics that actually say things about the users (althought posting time similarity and word similarity is definitely better than most metrics)
