import { useEffect, useMemo, useRef, useState } from "react";
import { GlobalWorkerOptions, getDocument } from "pdfjs-dist";
import type { PDFDocumentProxy } from "pdfjs-dist";
import workerUrl from "pdfjs-dist/build/pdf.worker.mjs?url";

import { getAuditJobDocumentUrl, getAuditJobParsedDocument } from "../api/auditJobs";
import type { Evidence, ParsedDocument } from "../types/audit";

GlobalWorkerOptions.workerSrc = workerUrl;

interface PdfEvidenceViewerProps {
  jobId: string;
  selectedEvidence: Evidence | null;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

export function PdfEvidenceViewer({ jobId, selectedEvidence }: PdfEvidenceViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [pdf, setPdf] = useState<PDFDocumentProxy | null>(null);
  const [parsedDocument, setParsedDocument] = useState<ParsedDocument | null>(null);
  const [pageNumber, setPageNumber] = useState(selectedEvidence?.page_number ?? 1);
  const [renderSize, setRenderSize] = useState({ width: 1, height: 1 });
  const [error, setError] = useState<string | null>(null);

  const documentUrl = useMemo(() => getAuditJobDocumentUrl(jobId), [jobId]);
  const currentPageLayout = parsedDocument?.pages.find((page) => page.page_number === pageNumber);

  useEffect(() => {
    let cancelled = false;
    setPdf(null);
    setParsedDocument(null);
    setError(null);
    setPageNumber(selectedEvidence?.page_number ?? 1);

    async function loadDocument() {
      try {
        const [nextPdf, nextParsedDocument] = await Promise.all([
          getDocument(documentUrl).promise,
          getAuditJobParsedDocument(jobId),
        ]);
        if (!cancelled) {
          setPdf(nextPdf);
          setParsedDocument(nextParsedDocument);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load PDF evidence view");
        }
      }
    }

    void loadDocument();
    return () => {
      cancelled = true;
    };
  }, [documentUrl, jobId, selectedEvidence?.page_number]);

  useEffect(() => {
    if (selectedEvidence) {
      setPageNumber(selectedEvidence.page_number);
    }
  }, [selectedEvidence]);

  useEffect(() => {
    if (!pdf || !canvasRef.current) {
      return;
    }

    let cancelled = false;
    const loadedPdf = pdf;
    async function renderPage() {
      const page = await loadedPdf.getPage(pageNumber);
      const viewport = page.getViewport({ scale: 1.35 });
      const canvas = canvasRef.current;
      if (!canvas || cancelled) {
        return;
      }
      const context = canvas.getContext("2d");
      if (!context) {
        return;
      }
      canvas.width = Math.floor(viewport.width);
      canvas.height = Math.floor(viewport.height);
      setRenderSize({ width: viewport.width, height: viewport.height });
      await page.render({ canvas, canvasContext: context, viewport }).promise;
    }

    void renderPage().catch((renderError) => {
      if (!cancelled) {
        setError(renderError instanceof Error ? renderError.message : "Unable to render PDF page");
      }
    });

    return () => {
      cancelled = true;
    };
  }, [pdf, pageNumber]);

  const highlightStyle = useMemo(() => {
    if (!selectedEvidence || !currentPageLayout || selectedEvidence.page_number !== pageNumber) {
      return null;
    }
    const { bbox } = selectedEvidence;
    const left = clamp(bbox.x0 / currentPageLayout.width, 0, 1) * renderSize.width;
    const top = clamp(bbox.y0 / currentPageLayout.height, 0, 1) * renderSize.height;
    const right = clamp(bbox.x1 / currentPageLayout.width, 0, 1) * renderSize.width;
    const bottom = clamp(bbox.y1 / currentPageLayout.height, 0, 1) * renderSize.height;
    return {
      left,
      top,
      width: Math.max(right - left, 2),
      height: Math.max(bottom - top, 2),
    };
  }, [currentPageLayout, pageNumber, renderSize.height, renderSize.width, selectedEvidence]);

  return (
    <div className="pdf-evidence-viewer">
      <div className="pdf-toolbar">
        <span>Page {pageNumber}{pdf ? ` / ${pdf.numPages}` : ""}</span>
        <div className="pdf-toolbar-actions">
          <button
            className="secondary-button compact-button"
            disabled={!pdf || pageNumber <= 1}
            onClick={() => setPageNumber((current) => Math.max(current - 1, 1))}
          >
            Previous
          </button>
          <button
            className="secondary-button compact-button"
            disabled={!pdf || pageNumber >= pdf.numPages}
            onClick={() => setPageNumber((current) => Math.min(current + 1, pdf?.numPages ?? current))}
          >
            Next
          </button>
        </div>
      </div>
      <div className="pdf-canvas-shell">
        <canvas ref={canvasRef} className="pdf-canvas" />
        {highlightStyle ? <div className="pdf-evidence-highlight" style={highlightStyle} /> : null}
      </div>
      {error ? (
        <div className="pdf-viewer-error">
          PDF precise viewer unavailable: {error}.{" "}
          <a href={documentUrl} target="_blank" rel="noreferrer">Open source PDF</a>
        </div>
      ) : null}
    </div>
  );
}
