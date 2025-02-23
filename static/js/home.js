// document.addEventListener("DOMContentLoaded", function () {
//     const searchInput = document.getElementById("searchInput");
//     const generateBtn = document.getElementById("generateBtn");
//     const voiceInputBtn = document.getElementById("voiceInputBtn");
//     const aiVoiceInputBtn = document.getElementById("aiVoiceInputBtn");
//     const speechModal = document.getElementById("speechRecognitionModal");
//     const aiModal = document.getElementById("aiProcessingModal");

//     function showModal(modal) {
//         modal.style.display = "flex";
//     }

//     function hideModal(modal) {
//         modal.style.display = "none";
//     }

//     async function generateImage() {
//         // 로그인 여부 체크 추가
//         if (!window.isUserAuthenticated) {
//             alert("로그인 후 사용 바랍니다.");
//             return;
//         }
//         const prompt = searchInput.value.trim();

//         if (!prompt) {
//             alert("프롬프트를 입력해주세요.");
//             return;
//         }

//         generateBtn.disabled = true;
//         const originalText = generateBtn.innerHTML;
//         generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 생성중...';

//         try {
//             const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
//             const response = await fetch("/app/ai/generate/", {
//                 method: "POST",
//                 headers: {
//                     "Content-Type": "application/x-www-form-urlencoded",
//                     "X-CSRFToken": csrfToken,
//                 },
//                 body: `prompt=${encodeURIComponent(prompt)}`,
//             });

//             if (!response.ok) {
//                 throw new Error("이미지 생성에 실패했습니다.");
//             }

//             const data = await response.json();

//             window.location.href = `/app/create/?${new URLSearchParams({
//                 image_url: data.image_url,
//                 generated_prompt: data.generated_prompt,
//                 original_prompt: prompt,
//             }).toString()}`;
//         } catch (error) {
//             alert(error.message);
//             console.error("Error:", error);
//         } finally {
//             generateBtn.disabled = false;
//             generateBtn.innerHTML = originalText;
//         }
//     }

//     function handleVoiceInput(useAI = false, user_style) {
//         if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) {
//             alert("이 브라우저는 음성 인식을 지원하지 않습니다.");
//             return;
//         }

//         const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
//         const recognition = new SpeechRecognition();
//         recognition.lang = "ko-KR";
//         recognition.interimResults = false;
//         recognition.maxAlternatives = 1;

//         recognition.start();
//         showModal(speechModal);

//         recognition.onresult = async function (event) {
//             const transcript = event.results[0][0].transcript;

//             hideModal(speechModal);

//             if (useAI) {
//                 showModal(aiModal);
//                 try {
//                     const response = await fetch("/app/ai/gpt4o/", {
//                         method: "POST",
//                         headers: {
//                             "Content-Type": "application/x-www-form-urlencoded",
//                             "X-CSRFToken": document.querySelector('[name="csrfmiddlewaretoken"]').value,
//                         },
//                         body: `text=${encodeURIComponent(transcript)}&style=${encodeURIComponent(user_style)}`,
//                     });

//                     if (!response.ok) throw new Error("AI 처리 실패");
//                     const data = await response.json();
//                     searchInput.value = data.result || transcript;
//                 } catch (error) {
//                     console.error("AI 처리 오류:", error);
//                     searchInput.value = transcript;
//                 } finally {
//                     hideModal(aiModal);
//                 }
//             } else {
//                 searchInput.value = transcript;
//             }
//         };

//         recognition.onerror = function (event) {
//             console.error("음성 인식 오류:", event.error);
//             hideModal(speechModal);
//             alert("음성 인식 중 오류가 발생했습니다.");
//         };

//         recognition.onend = function () {
//             hideModal(speechModal);
//         };
//     }

//     generateBtn.addEventListener("click", generateImage);
//     voiceInputBtn.addEventListener("click", () => handleVoiceInput(false)); // 기존 이벤트 핸들러
//     // 변경: data attribute를 사용하여 HTML에서 user_style 값을 읽어 전달
//     aiVoiceInputBtn.addEventListener("click", () => {
//         const user_style = aiVoiceInputBtn.getAttribute("data-user-style");
//         handleVoiceInput(true, user_style);
//     });

//     searchInput.addEventListener("keypress", function (e) {
//         if (e.key === "Enter") {
//             e.preventDefault();
//             generateImage();
//         }
//     });
// });
