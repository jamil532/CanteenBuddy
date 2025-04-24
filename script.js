document.getElementById("send-btn").addEventListener("click", function () {
    sendMessage(document.getElementById("user-input").value);
});

let phone_no = null;  // Store user phone number after registration

function sendMessage(message) {
    let chatBox = document.getElementById("chat-box");
    let userMessage = `<div class="chat-message user">${message}</div>`;
    chatBox.innerHTML += userMessage;
    
    document.getElementById("user-input").value = "";

    if (!phone_no && !message.startsWith("Register ")) {
        chatBox.innerHTML += `<div class="chat-message bot">Please register first by typing: Register <Your Name> <Your Phone></div>`;
        return;
    }

    if (message.toLowerCase().startsWith("register ")) {
        let parts = message.split(" ");
        if (parts.length < 3) {
            chatBox.innerHTML += `<div class="chat-message bot">Invalid format. Use: Register <Name> <Phone></div>`;
            return;
        }

        let name = parts[1];
        phone_no = parts[2];

        fetch("/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: name, phone_no: phone_no })
        })
        .then(response => response.json())
        .then(data => {
            chatBox.innerHTML += `<div class="chat-message bot">${data.message}</div>`;
        })
        .catch(error => console.error("Error:", error));

    } else if (message.toLowerCase() === "show menu") {
        fetch("/menu")
            .then(response => response.json())
            .then(data => {
                let menuMessage = `<div class="chat-message bot">Available Menu:<br>`;
                data.forEach(item => {
                    menuMessage += `🍽️ ${item.category} - ${item.item_name} - ₹${item.price} <br>`;
                });
                menuMessage += `</div>`;
                chatBox.innerHTML += menuMessage;
            });

    } else if (message.toLowerCase() === "order food") {
        chatBox.innerHTML += `<div class="chat-message bot">Please enter: Order <Item Name></div>`;

    } else if (message.toLowerCase().startsWith("order ")) {
        let itemName = message.substring(6);
        fetch("/order", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ phone_no: phone_no, item: itemName })
        })
        .then(response => response.json())
        .then(data => {
            chatBox.innerHTML += `<div class="chat-message bot">${data.message}</div>`;
        });

    } else if (message.toLowerCase() === "view bill") {
        fetch("/bill", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ phone_no: phone_no })
        })
        .then(response => response.json())
        .then(data => {
            let billMessage = `<div class="chat-message bot">Your Bill:<br>`;
            data.orders.forEach(item => {
                billMessage += `📌 ${item.item_name} - ₹${item.price} <br>`;
            });
            billMessage += `<b>Total: ₹${data.total}</b></div>`;
            chatBox.innerHTML += billMessage;
        });
    } else {
        chatBox.innerHTML += `<div class="chat-message bot">I didn't understand that. Please try again.</div>`;
    }

    chatBox.scrollTop = chatBox.scrollHeight;
}
