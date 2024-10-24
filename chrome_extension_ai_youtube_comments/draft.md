** # Project overview **
create a chrome extension that use claude sonnet 3.5 to reply youtube comments.


** # Core functionalities **
1. Get required number of youtube comments from the youtube video page. Do not use youtube api.
2. Use claude sonnet 3.5 to reply to the comments.
3. Display the replies in the youtube video page.

** # Doc **
1. Anthropic API typescript sdk
####
import Anthropic from "@anthropic-ai/sdk";

const anthropic = new Anthropic({
  // defaults to process.env["ANTHROPIC_API_KEY"]
  apiKey: "my_api_key",
});

const msg = await anthropic.messages.create({
  model: "claude-3-5-sonnet-20241022",
  max_tokens: 1000,
  temperature: 0,
  system: "You are an expert to reply Youtube comments.",
  messages: []
});
console.log(msg);
####


** # Current file structure **
xxxxx

** # Additional requirements **
xxxxx
