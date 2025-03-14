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

    sse.addEventListener("open", (event) => {
      this.gotEventSource();
    });

    sse.addEventListener("message", (event) => {
      for (let message of JSON.parse(event.data)) {
        this.addToChat(message);
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
    const message = {
      sender: "user",
      text: userInput,
      uuid: self.crypto.randomUUID(),
    };
    const userDiv = this.addToChat(message);
    userDiv.classList.add("unsent");
    userDiv.classList.add("unseen");

    const response = await fetch("api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(message),
    });
    if (response.status != 204) {
      return this.httpError(response);
    }

    userDiv.classList.remove("unsent");
  }

  addToChat({sender, text, html, uuid, timestamp}) {
    let div;
    if (uuid) {
      div = document.getElementById(uuid);
    }

    let newDiv;
    if (div) {
      div.className = "";
      div.innerText = "";
    } else {
      div = newDiv = document.createElement("div");
      if (uuid) {
        div.id = uuid;
      }
    }

    div.classList.add("message");
    div.classList.add(`from-${sender}`);

    const div2 = document.createElement("div");
    div2.classList.add("avatar");
    div.appendChild(div2);

    const div3 = document.createElement("div");
    if (html) {
        div3.innerHTML = DOMPurify.sanitize(html, {USE_PROFILES: {html: true}});
    } else {
        div3.innerText = text;
    }
    div.appendChild(div3);

    if (timestamp) {
        let datetime = new Date(timestamp);
        const div4 = document.createElement("div");
        div4.classList.add("timestamp");
        div4.innerText = datetime.toLocaleString("en-GB");
        div3.appendChild(div4);
    }

    if (newDiv) {
      const output = this.outputArea;
      output.appendChild(newDiv);
      output.scrollTop = output.scrollHeight - output.clientHeight;
    }

    return div3;
  }

  fatalError(message) {
    this.addToChat({
      sender: "error",
      text: message,
    });
  }

  httpError(response) {
    this.fatalError(`${response.status} ${response.statusText}`);
  }
}
