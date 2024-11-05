function fatalError(msg) {
  const main = document.getElementById("output");
  main.innerText = msg;
}

function httpError(response) {
  fatalError(`${response.status} ${response.statusText}`);
}

document.addEventListener("DOMContentLoaded", () => {
  getSession();
});

async function getSession() {
  const response = await fetch("api/login");
  if (response.status == 204) {
    return gotSession();
  }
  if (response.status != 200) {
    return httpError(response);
  }

  const csrf = document.getElementById("xov");

  const json = await response.json();
  csrf.value = json.csrf;

  const loginForm = document.getElementById("login");
  const user = document.getElementById("un");

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const pass = document.getElementById("pw");

    const response = await fetch("api/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user: user.value,
        pass: pass.value,
        csrf: csrf.value,
      }),
    });

    if (response.status == 204) {
      loginForm.style.display = "none";
      return gotSession();
    }
    if (response.status != 200) {
      return httpError(response);
    }

    const button = loginForm.getElementsByTagName("button")[0];
    button.style.backgroundColor = "red";

    const json = await response.json();
    csrf.value = json.csrf;

    user.focus();
  }, false);

  loginForm.style.display = "";
  user.focus();
}

function gotSession() {
  const outputArea = document.getElementById("output");
  const sse = new EventSource("api/events");

  sse.addEventListener("error", (event) => {
    fatalError("Event source didn't open😞");
  });
  sse.addEventListener("open", (event) => {
    gotEventSource(outputArea);
  });
  sse.addEventListener("message", (event) => {
    gotMessages(JSON.parse(event.data), outputArea);
  });
}

function gotEventSource(outputArea) {
  const form = document.getElementById("chat");
  const input = document.getElementById("input");

  form.addEventListener("submit", (event) => {
    event.preventDefault();

    let userInput = input.value;
    input.value = "";
    processInput(userInput, outputArea);
  }, false);

  const footer = document.getElementById("footer");
  footer.style.display = "";
  document.title = "H I V E";
  input.focus();
}

function gotMessages(messages, outputArea) {
  for (let message of messages) {
    addToChat(outputArea, message["sender"], message["text"], true);
  }
}

const apiEndpointURL = ("https://nrtt8bz8be.execute-api.us" +
                        "-east-1.amazonaws.com/prod/niall2");

async function processInput(userInput, messages) {
  userInput = userInput.trim();
  addToChat(messages, "user", userInput);

  const hiveDiv = addToChat(messages, "hive", "...");

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

  hiveDiv.innerText = json["niall_output"];
  hiveDiv.classList.remove("waiting");
}

function addToChat(messages, sender, message, noWait = false) {
  const div = document.createElement("div");
  div.classList.add("message");
  div.classList.add(`from-${sender}`);

  const div2 = document.createElement("div");
  div2.classList.add("avatar");
  div.appendChild(div2);

  const div3 = document.createElement("div");
  if (!noWait && sender == "hive") {
    div3.classList.add("waiting");
  }
  div3.innerText = message;
  div.appendChild(div3);

  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight - messages.clientHeight;
  return div3;
}
