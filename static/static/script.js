const API_KEY = "anurag-ai-123456789";

const sessionId = "anurag_" + Math.random().toString(36).substring(2, 10);

const chatBox = document.getElementById("chatBox");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const clearBtn = document.getElementById("clearBtn");
const typing = document.getElementById("typing");


function addMessage(message, type) {

    const messageDiv = document.createElement("div");

    messageDiv.className = "message " + type;

    if (type === "ai") {

        messageDiv.innerHTML = `
            <div class="avatar">🤖</div>
            <div class="bubble">${message}</div>
        `;

    } else {

        messageDiv.innerHTML = `
            <div class="bubble">${message}</div>
        `;
    }

    chatBox.appendChild(messageDiv);

    chatBox.scrollTop = chatBox.scrollHeight;
}


async function sendMessage() {

    const message = messageInput.value.trim();

    if (!message) {
        return;
    }

    addMessage(message, "user");

    messageInput.value = "";

    typing.style.display = "block";

    sendBtn.disabled = true;

    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            },

            body: JSON.stringify({
                session_id: sessionId,
                message: message
            })

        });


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail || "Something went wrong"
            );

        }


        addMessage(data.response, "ai");


    } catch (error) {

        addMessage(
            "❌ Error: " + error.message,
            "ai"
        );

    } finally {

        typing.style.display = "none";

        sendBtn.disabled = false;

        messageInput.focus();
    }
}


sendBtn.addEventListener("click", sendMessage);


messageInput.addEventListener("keydown", function(event) {

    if (event.key === "Enter") {
        sendMessage();
    }

});


clearBtn.addEventListener("click", async function() {

    try {

        await fetch(
            `/clear-memory/${sessionId}`,
            {
                method: "DELETE",
                headers: {
                    "X-API-Key": API_KEY
                }
            }
        );

        chatBox.innerHTML = "";

        addMessage(
            "Chat cleared. How can I help you?",
            "ai"
        );

    } catch (error) {

        addMessage(
            "❌ Could not clear chat.",
            "ai"
        );

    }

});
