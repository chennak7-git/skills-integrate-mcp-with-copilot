document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const signupContainer = document.getElementById("signup-container");
  const messageDiv = document.getElementById("message");
  const accountButton = document.getElementById("account-button");
  const accountAction = document.getElementById("account-action");
  const loginDialog = document.getElementById("login-dialog");
  const loginForm = document.getElementById("login-form");
  const loginError = document.getElementById("login-error");
  const cancelLoginButton = document.getElementById("cancel-login");
  let teacherUsername = null;

  function showMessage(element, message, type) {
    element.textContent = message;
    element.className = `message ${type}`;
    window.setTimeout(() => element.classList.add("hidden"), 5000);
  }

  function updateAuthUI(username) {
    teacherUsername = username;
    const isTeacher = Boolean(username);
    signupContainer.classList.toggle("hidden", !isTeacher);
    accountAction.textContent = isTeacher ? `Sign out (${username})` : "Teacher sign in";
    accountButton.setAttribute(
      "aria-label",
      isTeacher ? `Sign out ${username}` : "Teacher sign in"
    );
  }

  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      if (!response.ok) {
        throw new Error("Activity request failed");
      }
      const activities = await response.json();
      activitiesList.replaceChildren();
      activitySelect.replaceChildren(new Option("-- Select an activity --", ""));

      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";
        const spotsLeft =
          details.max_participants - details.participants.length;
        const title = document.createElement("h4");
        title.textContent = name;
        const description = document.createElement("p");
        description.textContent = details.description;
        const schedule = document.createElement("p");
        const scheduleLabel = document.createElement("strong");
        scheduleLabel.textContent = "Schedule: ";
        schedule.append(scheduleLabel, document.createTextNode(details.schedule));
        const availability = document.createElement("p");
        const availabilityLabel = document.createElement("strong");
        availabilityLabel.textContent = "Availability: ";
        availability.append(
          availabilityLabel,
          document.createTextNode(`${spotsLeft} spots left`)
        );
        const participantsContainer = document.createElement("div");
        participantsContainer.className = "participants-container";
        const participantsHeading = document.createElement("h5");
        participantsHeading.textContent = "Participants:";
        participantsContainer.appendChild(participantsHeading);

        if (details.participants.length > 0) {
          const participantsList = document.createElement("ul");
          participantsList.className = "participants-list";
          details.participants.forEach((email) => {
            const participant = document.createElement("li");
            const participantEmail = document.createElement("span");
            participantEmail.className = "participant-email";
            participantEmail.textContent = email;
            participant.appendChild(participantEmail);

            if (teacherUsername) {
              const unregisterButton = document.createElement("button");
              unregisterButton.className = "delete-btn";
              unregisterButton.type = "button";
              unregisterButton.textContent = "Remove";
              unregisterButton.setAttribute("aria-label", `Remove ${email} from ${name}`);
              unregisterButton.dataset.activity = name;
              unregisterButton.dataset.email = email;
              participant.appendChild(unregisterButton);
            }
            participantsList.appendChild(participant);
          });
          participantsContainer.appendChild(participantsList);
        } else {
          const emptyMessage = document.createElement("p");
          emptyMessage.innerHTML = "<em>No participants yet</em>";
          participantsContainer.appendChild(emptyMessage);
        }

        activityCard.append(title, description, schedule, availability, participantsContainer);
        activitiesList.appendChild(activityCard);

        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

    } catch (error) {
      const errorMessage = document.createElement("p");
      errorMessage.textContent = "Failed to load activities. Please try again later.";
      activitiesList.replaceChildren(errorMessage);
      console.error("Error fetching activities:", error);
    }
  }

  async function handleUnregister(button) {
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();
      if (response.ok) {
        showMessage(messageDiv, result.message, "success");
        await fetchActivities();
      } else {
        showMessage(messageDiv, result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage(messageDiv, "Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  activitiesList.addEventListener("click", (event) => {
    const button = event.target.closest(".delete-btn");
    if (button) {
      handleUnregister(button);
    }
  });

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(messageDiv, result.message, "success");
        signupForm.reset();
        await fetchActivities();
      } else {
        showMessage(messageDiv, result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage(messageDiv, "Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  accountButton.addEventListener("click", async () => {
    if (!teacherUsername) {
      loginError.classList.add("hidden");
      loginDialog.showModal();
      return;
    }

    try {
      const response = await fetch("/auth/logout", { method: "POST" });
      if (!response.ok) {
        throw new Error("Sign out failed");
      }
      updateAuthUI(null);
      await fetchActivities();
    } catch (error) {
      showMessage(messageDiv, "Failed to sign out. Please try again.", "error");
      console.error("Error signing out:", error);
    }
  });

  cancelLoginButton.addEventListener("click", () => loginDialog.close());

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    loginError.classList.add("hidden");
    const credentials = {
      username: document.getElementById("username").value,
      password: document.getElementById("password").value,
    };

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(credentials),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Sign in failed");
      }

      loginForm.reset();
      loginDialog.close();
      updateAuthUI(result.username);
      await fetchActivities();
    } catch (error) {
      loginError.textContent = error.message;
      loginError.classList.remove("hidden");
    }
  });

  async function loadTeacherSession() {
    try {
      const response = await fetch("/auth/session");
      const session = await response.json();
      updateAuthUI(session.authenticated ? session.username : null);
    } catch (error) {
      updateAuthUI(null);
      console.error("Error checking teacher session:", error);
    }
    await fetchActivities();
  }

  loadTeacherSession();
});
