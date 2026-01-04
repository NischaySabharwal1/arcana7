// background.js

import { runLocalLLM } from './llm_handler.js';

const USE_LOCAL_LLM = true; // Set to true to enable local LLM, false to keep local LLM logic, but prevent calls for testing

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "simplifai",
    title: "SimplifAI",
    contexts: ["selection"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "simplifai") {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: getSelectedText,
    }, (results) => {
      if (results && results[0] && results[0].result) {
        const selectedText = results[0].result;
        processSelectedText(selectedText, tab.id);
      } else {
        console.error(`[SimplifAI] Error: No text selected or content script failed to return text in tab ${tab.id}.`);
        chrome.scripting.executeScript({
            target: { tabId: tab.id },
            function: displayResultOnPage,
            args: ["No text selected."]
        });
      }
    });
  }
});

function getSelectedText() {
  return window.getSelection().toString();
}

// New function to display results directly in the content script context
function displayResultOnPage(resultText) {
  const resultDiv = document.createElement("div");
  resultDiv.style.cssText = "position: fixed; top: 10px; right: 10px; background-color: lightyellow; padding: 10px; border: 1px solid grey; z-index: 99999; color: black; cursor: pointer;"; // Added black text color and cursor pointer
  resultDiv.textContent = resultText;
  document.body.appendChild(resultDiv);

  // Remove the result when clicked
  resultDiv.addEventListener('click', () => {
    resultDiv.remove();
  });
}

// Main processing logic
async function processSelectedText(selectedText, tabId) {
  if (!selectedText) {
    console.warn(`[SimplifAI] No text selected in tab ${tabId}.`);
    chrome.scripting.executeScript({
        target: { tabId: tabId },
        function: displayResultOnPage,
        args: ["No text selected."]
    });
    return;
  }
  console.log(`[${new Date().toLocaleTimeString()}] [SimplifAI] Text received for processing in tab ${tabId}:`, selectedText);

  const data = await chrome.storage.sync.get(['defaultLanguage', 'ollamaApiEndpoint', 'ollamaModel']);
  const defaultLanguage = data.defaultLanguage || 'en';
  const ollamaApiEndpoint = data.ollamaApiEndpoint;
  const ollamaModel = data.ollamaModel;

  let processedResult = "";
  let detectedLanguage = '';

  if (!USE_LOCAL_LLM) {
    console.error("[SimplifAI] Error: Local LLM is disabled. Cannot process text.");
    chrome.scripting.executeScript({
        target: { tabId: tabId },
        function: displayResultOnPage,
        args: ["Error: Local LLM is disabled. Please enable it in background.js for development."]
    });
    return;
  }

  // Attempt language detection with local LLM (Ollama)
  try {
    console.log("[SimplifAI] Attempting local LLM (Ollama) language detection...");
    detectedLanguage = await runLocalLLM(selectedText, 'detect_language', defaultLanguage, ollamaApiEndpoint, ollamaModel);
    console.log("[SimplifAI] Local LLM (Ollama) detected language:", detectedLanguage);
  } catch (llmError) {
    console.error("[SimplifAI] Local LLM (Ollama) language detection failed:", llmError.message);
    chrome.scripting.executeScript({
        target: { tabId: tabId },
        function: displayResultOnPage,
        args: [`Error with Ollama (detection): ${llmError.message}. Is Ollama running and model installed?`]
    });
    return;
  }

  // Now, attempt translation or simplification with local LLM (Ollama)
  try {
    if (detectedLanguage === 'en' || detectedLanguage === defaultLanguage) {
      console.log("[SimplifAI] Attempting local LLM (Ollama) simplification...");
      processedResult = await runLocalLLM(selectedText, 'simplify', defaultLanguage, ollamaApiEndpoint, ollamaModel);
    } else {
      console.log("[SimplifAI] Attempting local LLM (Ollama) translation...");
      processedResult = await runLocalLLM(selectedText, 'translate', defaultLanguage, ollamaApiEndpoint, ollamaModel);
    }
  } catch (llmError) {
    console.error("[SimplifAI] Local LLM (Ollama) translation/simplification failed:", llmError.message);
    chrome.scripting.executeScript({
        target: { tabId: tabId },
        function: displayResultOnPage,
        args: [`Error with Ollama (processing): ${llmError.message}. Is Ollama running and model installed?`]
    });
    return;
  }

  console.log(`[${new Date().toLocaleTimeString()}] [SimplifAI] Sending result to tab ${tabId}:`, processedResult);
  chrome.scripting.executeScript({
      target: { tabId: tabId },
      function: displayResultOnPage,
      args: [processedResult]
  });
}

chrome.runtime.onMessage.addListener(async (request, sender, sendResponse) => {
  if (request.action === "processText") {
    console.warn("[SimplifAI] Received unexpected 'processText' message in onMessage listener. This should not happen with current architecture.");
  }
});
