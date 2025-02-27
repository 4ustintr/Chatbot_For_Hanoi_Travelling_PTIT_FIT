function animateButton() {
    var openButton = document.getElementById("open-chatbot");
    openButton.style.transform = "translate(-50%, -50%) scale(0.8)";
    openButton.style.opacity = "0";
    setTimeout(() => {
        openButton.style.visibility = "hidden";
        toggleChat(true);
    }, 300);
}

function toggleChat(open) {
    var chatbox = document.getElementById("chatbot");
    if (open) {
        chatbox.classList.add("show");
    } else {
        chatbox.classList.remove("show");
        setTimeout(() => {
            var openButton = document.getElementById("open-chatbot");
            openButton.style.visibility = "visible";
            openButton.style.opacity = "1";
            openButton.style.transform = "translate(-50%, -50%) scale(1)";
        }, 300);
    }
}

function formatMessage(text) {
    text = text.replace(/\n/g, '<br>');
    
    text = text.replace(/^# (.*$)/gm, '<h1>$1</h1>');
    text = text.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    text = text.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    
    text = text.replace(/^- (.+)$/gm, '• $1');
    
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    text = text.replace(/\_(.+?)\_/g, '<em>$1</em>');
    
    text = text.replace(/([🏷️📍💰⭐⏰🔍])/g, '<span class="emoji">$1</span>');
    
    return text;
}


function updateLanguage() {
    
    currentLanguage = languageSelect.value;
    
    const input = document.getElementById('user-input');
    switch(currentLanguage) {
        case 'vi':
            input.placeholder = 'Nhập tin nhắn...';
            break;
        case 'ja':
            input.placeholder = 'メッセージを入力...';
            break;
        default:
            input.placeholder = 'Type your message...';
    }
}

function createDestinationPopup(title, description, coordinates, imageUrl) {
    const popup = document.createElement('div');
    popup.className = 'destination-popup';
    
    const closeBtn = document.createElement('button');
    closeBtn.className = 'popup-close';
    closeBtn.innerHTML = '×';
    closeBtn.onclick = () => popup.remove();
    
    const content = document.createElement('div');
    content.className = 'popup-content';
    
    const titleElem = document.createElement('h2');
    titleElem.textContent = title;
    
    const descElem = document.createElement('p');
    descElem.textContent = description;
    
    const image = document.createElement('img');
    image.src = imageUrl;
    image.className = 'popup-image';
    
    const mapContainer = document.createElement('div');
    mapContainer.id = 'map';
    mapContainer.style.height = '300px';
    
    content.appendChild(titleElem);
    content.appendChild(image);
    content.appendChild(descElem);
    content.appendChild(mapContainer);
    popup.appendChild(closeBtn);
    popup.appendChild(content);
    
    document.body.appendChild(popup);
    
    const map = L.map('map').setView(coordinates, 15);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    L.marker(coordinates).addTo(map);
    
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position) => {
            const userLocation = [position.coords.latitude, position.coords.longitude];
            
            L.marker(userLocation).addTo(map)
                .bindPopup('Your Location')
                .openPopup();
                waypoints: [
                    L.latLng(userLocation),
                    L.latLng(coordinates)
                ],
            L.Routing.control({
                waypoints: [
                    L.latLng(userLocation),
                    L.latLng(coordinates)
                ],
                routeWhileDragging: true,
                showAlternatives: false,
                show: false,
                collapsible: true,
                lineOptions: {
                styles: [
                    {color: 'blue', opacity: 0.6, weight: 4}
                ]
                }
            }).addTo(map);
        });
    }
}
const languageSelect = document.getElementById('languageSelect');
languageSelect.addEventListener('change', updateLanguage);

document.addEventListener('DOMContentLoaded', () => {
    updateLanguage();
});
document.addEventListener('DOMContentLoaded', () => {
    const destinations = {
        'Hoan Kiem Lake': {
            coordinates: [21.0285, 105.8522],
            description: 'A historic heart of Hanoi with the iconic Turtle Tower.',
            image: 'static/landingpage/hgdes.jpg'
        },
        'Long Bien Bridge': {
            coordinates: [21.0435, 105.8508],
            description: 'Historic bridge spanning the Red River, built during French colonial period.',
            image: 'static/landingpage/long_bien.jpg'
        },
        'The Temple of Literature': {
            coordinates: [21.0293, 105.8354],
            description: 'Vietnam\'s first national university, dating back to 1070.',
            image: 'static/landingpage/vmdes.jpg'
        },
        'Hanoi Old Quarter': {
            coordinates: [21.0338, 105.8500],
            description: 'Historic heart of Hanoi, featuring 36 streets of traditional crafts and commerce.',
            image: 'static/landingpage/pcdes.jpg'
        }
    };

    const cards = document.querySelectorAll('.destination-card');
    cards.forEach(card => {
        card.addEventListener('click', () => {
            const title = card.querySelector('h3').textContent;
            const dest = destinations[title];
            if (dest) {
                createDestinationPopup(title, dest.description, dest.coordinates, dest.image);
            }
        });
    });
});

async function sendMessage(event) {
    if (event && event.key !== "Enter") return;

    var userInput = document.getElementById("user-input").value;
    if (!userInput.trim()) return;

    var chatBody = document.getElementById("chat-body");
    var userMessage = document.createElement("div");
    userMessage.className = "user-message message";
    userMessage.textContent = userInput;
    chatBody.appendChild(userMessage);

    document.getElementById("user-input").value = "";
    chatBody.scrollTop = chatBody.scrollHeight;

    try {
        const response = await fetch('http://localhost:8000/bot/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: userInput,
                language: languageSelect.value
            })
        });
    
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        const messageDiv = document.createElement("div");
        messageDiv.className = "bot-message message";
        chatBody.appendChild(messageDiv);
        let fullMessage = '';
    
        try {
            while (true) {
                const {value, done} = await reader.read();
                if (done) break;
                
                const text = decoder.decode(value);
                const lines = text.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const jsonContent = JSON.parse(line.slice(6));
                        
                        if (jsonContent.complete) {
                            fullMessage = jsonContent.response;
                            // Store the complete response data for later use
                            window.lastJsonContent = jsonContent;
                        } else if (jsonContent.response) {
                            fullMessage += jsonContent.response;
                        }
                        
                        messageDiv.innerHTML = window.marked ?
                            window.marked.parse(fullMessage) :
                            fullMessage;
                        messageDiv.classList.add('markdown-content');
                    }
                }
            }
        } catch (error) {
            console.error('Error reading stream:', error);
        } finally {
            reader.releaseLock();
                        const coordsMatch = fullMessage.match(/GPS Coordinates: (-?\d+\.\d+), (-?\d+\.\d+)/);
            if (coordsMatch) {
                const lat = parseFloat(coordsMatch[1]);
                const lng = parseFloat(coordsMatch[2]);
                const mapContainer = document.createElement('div');
                mapContainer.style.height = '300px';
                mapContainer.style.marginTop = '10px';
                messageDiv.appendChild(mapContainer);
                
                const map = L.map(mapContainer).setView([lat, lng], 15);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                }).addTo(map);
                
                L.marker([lat, lng]).addTo(map);
                
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition((position) => {
                        const userLocation = [position.coords.latitude, position.coords.longitude];
                        
                        L.marker(userLocation).addTo(map)
                            .bindPopup('Your Location')
                            .openPopup();
                        
                        L.Routing.control({
                            waypoints: [
                                L.latLng(userLocation),
                                L.latLng([lat, lng])
                            ],
                            routeWhileDragging: true,
                            showAlternatives: false,
                            show: false,
                            collapsible: true,
                            lineOptions: {
                                styles: [{color: 'blue', opacity: 0.6, weight: 4}]
                            }
                        }).addTo(map);
                    });
                }
                
                chatBody.scrollTop = chatBody.scrollHeight;
            }

            // Add images after the map if they exist in the complete response
            if (window.lastJsonContent && window.lastJsonContent.images && window.lastJsonContent.images.length > 0) {
                const imageGallery = document.createElement('div');
                imageGallery.className = 'image-gallery';
                imageGallery.style.marginTop = '20px';
                
                window.lastJsonContent.images.forEach(imageUrl => {
                    const imgContainer = document.createElement('div');
                    imgContainer.className = 'image-container';
                    const img = document.createElement('img');
                    img.src = imageUrl;
                    img.alt = 'Location image';
                    img.className = 'location-image';
                    img.onerror = () => {
                        imgContainer.remove();
                    };
                    
                    // Add click handler to show image popup
                    img.onclick = () => {
                        createImagePopup(imageUrl);
                    };
                    
                    imgContainer.appendChild(img);
                    imageGallery.appendChild(imgContainer);
                });
                
                messageDiv.appendChild(imageGallery);
                chatBody.scrollTop = chatBody.scrollHeight;
            }

function createImagePopup(imageUrl) {
    const overlay = document.createElement('div');
    overlay.className = 'image-popup-overlay';
    
    const img = document.createElement('img');
    img.src = imageUrl;
    img.className = 'image-popup-img';
    
    overlay.appendChild(img);
    document.body.appendChild(overlay);
    
    // Click anywhere (including the image) to close
    overlay.addEventListener('click', () => {
        overlay.remove();
    });
}
            // Clean up the stored response data
            window.lastJsonContent = null;
        }
    } catch (error) {
        var errorMessage = document.createElement("div");
        errorMessage.className = "bot-message message error";
        errorMessage.textContent = "Sorry, I encountered an error while processing your message.";
        chatBody.appendChild(errorMessage);
        chatBody.scrollTop = chatBody.scrollHeight;
        console.error('Error:', error);
    }
}