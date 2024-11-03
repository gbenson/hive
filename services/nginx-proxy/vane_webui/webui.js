document.addEventListener("DOMContentLoaded", () => {
  const main = document.getElementsByTagName("main")[0];
  const form = document.getElementsByTagName("form")[0];
  const input = form.getElementsByTagName("input")[0];

  form.addEventListener("submit", (event) => {
    event.preventDefault();

    let userInput = input.value;
    input.value = "";
    processInput(userInput, main);
  }, false);

});

const apiEndpointURL = ("https://nrtt8bz8be.execute-api.us" +
                        "-east-1.amazonaws.com/prod/niall2");

async function processInput(userInput, messages) {
  userInput = userInput.trim();
  addToChat(messages, "user", userInput);

  const niallDiv = addToChat(messages, "niall", "...");

  const response = await fetch(apiEndpointURL, {
    method: "POST",
    headers: {
      // "application/json" would be better here, but
      // then CORS preflights every single request :(
      "Content-Type": "text/plain",
    },
    body: JSON.stringify({
      user_input: userInput,
    }),
  });
  const json = await response.json();

  niallDiv.innerText = json["niall_output"];
  niallDiv.classList.remove("waiting");
}

function addToChat(messages, sender, message) {
  const div = document.createElement("div");
  div.classList.add("message");
  div.classList.add(`from-${sender}`);

  const div2 = document.createElement("div");
  div2.classList.add("avatar");
  div.appendChild(div2);

  const div3 = document.createElement("div");
  if (sender == "niall") {
    div3.classList.add("waiting");
  }
  div3.innerText = message;
  div.appendChild(div3);

  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight - messages.clientHeight;
  return div3;
}
