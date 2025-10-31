"use client";

import React, { useRef, useState } from "react";
import { Upload, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { uploadPdfDocument } from "@/util/uploadPdfDocument";
import { Resource } from "@/types/resources";

interface UploadIntakeTabProps {
  userEmail: string;
  onResources: (resources: Resource[]) => void;
}

export function UploadIntakeTab({ userEmail, onResources }: UploadIntakeTabProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isPdfProcessing, setIsPdfProcessing] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);

  const handleFileUploadSingle = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    console.log("File input changed", event.target.files);
    const file = event.target.files?.[0];
    if (file) {
      const supportedTypes = ["application/pdf"];

      if (supportedTypes.includes(file.type)) {
        setUploadedFile(file);
        setPdfError(null);
        setIsPdfProcessing(true);

        try {
          const resources = await uploadPdfDocument(userEmail, file);
          onResources(resources);
        } catch (error) {
          console.error("Error processing PDF:", error);
          setPdfError(
            error instanceof Error ? error.message : "Failed to process PDF",
          );
        } finally {
          setIsPdfProcessing(false);
        }
      } else {
        setPdfError("Please upload a PDF file.");
      }
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <>
      {!uploadedFile ? (
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={(e) => void handleFileUploadSingle(e)}
            className="hidden"
            id="file-upload"
          />
          <div className="flex flex-col items-center">
            <Upload className="w-12 h-12 mb-4" />
            <span className="text-lg font-medium text-gray-600 mb-2">
              Upload a PDF of typed client information. Our AI will
              automatically extract client information and generate relevant
              referrals.
            </span>
            <Button
              type="button"
              onClick={triggerFileInput}
              className="bg-blue-600 hover:bg-blue-700"
              disabled={isPdfProcessing}
            >
              Select a PDF file
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileText className="w-8 h-8 text-blue-600" />
                <div>
                  <p className="font-medium text-gray-900">
                    {uploadedFile.name}
                  </p>
                  <p className="text-sm text-gray-500">
                    {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
            </div>
          </div>

          {isPdfProcessing && (
            <div className="flex items-center justify-center p-8 bg-blue-50 border border-blue-200 rounded-lg">
              <Spinner className="mr-3" />
              <span className="text-blue-700 font-medium">
                Processing PDF and generating referrals...
              </span>
            </div>
          )}

          {pdfError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 font-medium">Error: {pdfError}</p>
              <Button
                type="button"
                onClick={() => {
                  setUploadedFile(null);
                  setPdfError(null);
                }}
                variant="outline"
                className="mt-3"
              >
                Try Again
              </Button>
            </div>
          )}
        </div>
      )}
    </>
  );
}
