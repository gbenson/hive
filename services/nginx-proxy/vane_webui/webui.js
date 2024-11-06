document.addEventListener("DOMContentLoaded", () => {
  const app = new WebUI();
  app.run();
});

class WebUI {
  outputArea = document.getElementById("output");

  run() {
    this.getSession();
  }

  async getSession() {
    const response = await fetch("api/login");
    if (response.status == 204) {
      return this.gotSession();
    }
    if (response.status != 200) {
      return this.httpError(response);
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
        return this.gotSession();
      }
      if (response.status != 200) {
        return this.httpError(response);
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

  gotSession() {
    const sse = new EventSource("api/events");

    sse.addEventListener("error", (event) => {
      this.fatalError("Event source didn't open😞");
    });

    sse.addEventListener("open", (event) => {
      this.gotEventSource();
    });

    sse.addEventListener("message", (event) => {
      for (let message of JSON.parse(event.data)) {
        this.addToChat(message["sender"], message["text"]);
      }
    });
  }

  gotEventSource() {
    const form = document.getElementById("chat");
    const input = document.getElementById("input");

    form.addEventListener("submit", (event) => {
      event.preventDefault();

      let userInput = input.value;
      input.value = "";
      this.processInput(userInput);
    }, false);

    const footer = document.getElementById("footer");
    footer.style.display = "";
    document.title = "H I V E";
    input.focus();
  }

  async processInput(userInput) {
    userInput = userInput.trim();
    this.addToChat("user", userInput);

    const hiveDiv = this.addToChat("hive", "...");
    hiveDiv.classList.add("waiting");

    const apiEndpointURL = ("https://nrtt8bz8be.execute-api.us" +
                            "-east-1.amazonaws.com/prod/niall2");

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
    if (response.status != 200) {
      return this.httpError(response);
    }

    const json = await response.json();

    hiveDiv.innerText = json["niall_output"];
    hiveDiv.classList.remove("waiting");
  }

  addToChat(sender, message) {
    const div = document.createElement("div");
    div.classList.add("message");
    div.classList.add(`from-${sender}`);

    const div2 = document.createElement("div");
    div2.classList.add("avatar");
    div.appendChild(div2);

    const div3 = document.createElement("div");
    div3.innerText = message;
    div.appendChild(div3);

    const output = this.outputArea;
    output.appendChild(div);
    output.scrollTop = output.scrollHeight - output.clientHeight;

    return div3;
  }

  fatalError(message) {
    this.addToChat("error", message);
  }

  httpError(response) {
    this.fatalError(`${response.status} ${response.statusText}`);
  }
}
