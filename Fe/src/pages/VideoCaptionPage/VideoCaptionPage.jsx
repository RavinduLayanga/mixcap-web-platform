import React, { useState, useRef } from "react";
import axios from "axios";
import "./VideoCaptionPage.css";


const VideoCaptionPage = () => {
  const [file, setFile] = useState(null);
  const [videoURL, setVideoURL] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [generatedCaptions, setGeneratedCaptions] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [filename, setFilename] = useState(""); 
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (!selected) return;

    if (!selected.type.includes("video")) {
      alert("Please upload a valid video file.");
      return;
    }

    if (selected.size > 200 * 1024 * 1024) {
      alert("File size exceeds 200MB limit.");
      return;
    }

    // Sanitize filename: remove spaces and unsafe characters
    const originalName = selected.name;
    const safeName = originalName.replace(/[^\w-.]/g, "_");
    const renamedFile = new File([selected], safeName, { type: selected.type });

    setFile(renamedFile);
    setFilename(safeName);  
    setUploadProgress(0);
    setVideoURL(URL.createObjectURL(renamedFile));
    setGeneratedCaptions("");
  };

  const handleGenerateCaptions = async () => {
    if (!file) {
      alert("Please upload a video first.");
      return;
    }

    const formData = new FormData();
    formData.append("video", file);

    setIsLoading(true);
    setGeneratedCaptions("Uploading video...");

    try {
      // === 1. Upload video ===
      await axios.post("http://127.0.0.1:5000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percent);
        },
      });

      setGeneratedCaptions("Extracting features...");

      // === 2. Extract features ===
      await axios.post("http://127.0.0.1:5000/extract_features", {
        filename: file.name,
      });

      setGeneratedCaptions("Generating caption...");

      // === 3. Generate caption ===
      const response = await axios.post("http://127.0.0.1:5000/generate_caption", {
        filename: file.name,
      });

      setGeneratedCaptions(response.data.caption || "No caption returned.");
    } catch (error) {
      setGeneratedCaptions("Error: " + (error.response?.data?.error || error.message));
    }

    setIsLoading(false);
  };

  const handleSave = async () => {
    if (!filename || !generatedCaptions) {
      alert("Missing filename or generated caption.");
      return;
    }

    try {
      const response = await axios.post("http://127.0.0.1:5000/save_caption", {
        filename: filename,
        caption: generatedCaptions,
      });

      alert(response.data.message || "Saved successfully.");
    } catch (error) {
      alert("Save failed: " + (error.response?.data?.error || error.message));
    }
  };



  const copyCaptions = () => {
  if (!generatedCaptions || generatedCaptions.trim() === "") {
    alert("No caption to copy.");
    return;
  }

  navigator.clipboard.writeText(generatedCaptions)
    .then(() => {
      alert("Caption copied to clipboard.");
    })
    .catch((err) => {
      alert("Failed to copy caption.");
      console.error("Copy error:", err);
    });
};


  const handleClear = () => {
    setFile(null);
    setVideoURL("");
    setUploadProgress(0);
    setGeneratedCaptions("");
    setFilename("");

  // Reset input element value
  if (fileInputRef.current) {
    fileInputRef.current.value = null;
  }
  };

  return (
    <div className="video-caption-page">
      <div className="upload-section">
        <div className="upload-box">
          <p className="upload-text">Drag and drop your video here</p>
          <p className="upload-or">or</p>
          <input ref={fileInputRef} type="file" accept="video/*" onChange={handleFileChange} />
          <p className="upload-info">MP4, MOV up to 200MB</p>

          {uploadProgress > 0 && (
            <div className="upload-progress">
              <div className="progress-bar" style={{ width: `${uploadProgress}%` }} />
              <p className="progress-text">Uploading video... {uploadProgress}%</p>
            </div>
          )}

          {videoURL && (
            <video src={videoURL} controls className="video-preview" />
          )}
        </div>
      </div>

      <button className="generate-button" onClick={handleGenerateCaptions} disabled={isLoading}>
        {isLoading ? "Generating..." : "Generate Captions"}
      </button>

      <div className="results-section">
        <div className="results-header">
          <h3>Generated Captions</h3>
          <button className="copy-button" onClick={copyCaptions}>Copy</button>
        </div>
        <div className="captions-box">
          {generatedCaptions || "The generated captions will appear here..."}
        </div>
      </div>

      <div className="export-options">
        <button className="export-button" onClick={() => downloadText(generatedCaptions)}>Download as Text</button>
        <button className="export-button" onClick={() => downloadJSON(generatedCaptions)}>Export JSON</button>
      </div>

      <div className="clear-save-buttons">
        <button className="export-button" onClick={handleClear}>Clear</button>
        <button className="export-button" onClick={handleSave}>Save</button>
      </div>
    </div>
  );
};



function downloadText(text) {
  if (!text || text.trim() === "") {
    alert("No caption to download.");
    return;
  }

  const blob = new Blob([text], { type: "text/plain" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "captions.txt";
  link.click();
}


// function downloadJSON(text) {
//   const blob = new Blob([JSON.stringify({ caption: text }, null, 2)], { type: "application/json" });
//   const link = document.createElement("a");
//   link.href = URL.createObjectURL(blob);
//   link.download = "captions.json";
//   link.click();
// }

function downloadJSON(text) {
  if (!text || text.trim() === "") {
    alert("No caption to export.");
    return;
  }

  const blob = new Blob([JSON.stringify({ caption: text }, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "captions.json";
  link.click();
}


export default VideoCaptionPage;
