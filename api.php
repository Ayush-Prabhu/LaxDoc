<?php
require('fpdf.php');
header("Content-Type: application/json");

// Suppress warnings and deprecations
error_reporting(E_ALL & ~E_DEPRECATED & ~E_WARNING);
ini_set('display_errors', 0);
ini_set('log_errors', 1);
ini_set('error_log', 'error_log.txt');

$action = $_POST['action'] ?? $_GET['action'] ?? '';

switch ($action) {
    case 'importTemplate':
        importTemplate();
        break;
    case 'exportTemplate':
        exportTemplate();
        break;
    case 'deleteTemplate':
        deleteTemplate();
        break;
    case 'getTemplates':
        getTemplates();
        break;
    case 'generateDocument':
        generateDocument();
        break;
    case 'searchDocuments':
        searchDocuments();
        break;
    case 'regenerateDocument':
        regenerateDocument();
    default:
        echo json_encode(["success" => false, "error" => "Invalid action"]);
}

function regenerateDocument()
{
    if ($_POST['action'] === 'regenerateDocument') {
        $documentId = $_POST['documentId'] ?? '';
        
        if (!$documentId) {
            echo json_encode(['success' => false, 'error' => 'Missing document ID']);
            exit;
        }
    
        $documentsDir = __DIR__ . '/documents/';
        $templatesDir = __DIR__ . '/templates/';
        $csvFile = __DIR__ . '/templates.csv';
    
        // Find the document file
        $documentFile = findDocumentById($documentId, $documentsDir);
        if (!$documentFile) {
            echo json_encode(['success' => false, 'error' => 'Document not found']);
            exit;
        }
    
        // Find corresponding template
        $templateFile = findTemplateForDocument($documentFile, $csvFile, $templatesDir);
        if (!$templateFile) {
            echo json_encode(['success' => false, 'error' => 'Template not found in CSV']);
            exit;
        }
    
        // Generate the document again
        $outputFile = $documentsDir . "regenerated_" . basename($documentFile) . ".pdf";
        $success = generateDocumentAgain($templateFile, $documentFile, $outputFile);
    
        if ($success) {
            echo json_encode(['success' => true, 'message' => 'Document regenerated successfully', 'pdf_url' => $outputFile]);
        } else {
            echo json_encode(['success' => false, 'error' => 'Failed to regenerate document']);
        }
        exit;
    }
    
}

function findDocumentById($documentId, $documentsDir) {
    $files = scandir($documentsDir);
    foreach ($files as $file) {
        if (strpos($file, $documentId) !== false) {
            return $documentsDir . $file;
        }
    }
    return false;
}
function findTemplateForDocument($documentFile, $csvFile, $templatesDir) {
    if (!file_exists($csvFile)) {
        error_log("CSV file not found: $csvFile");
        return false;
    }

    $target = trim(basename($documentFile));
    error_log("Looking for document: '$target' in CSV");

    $handle = fopen($csvFile, 'r');
    if (!$handle) {
        error_log("Failed to open CSV file: $csvFile");
        return false;
    }

    while (($row = fgetcsv($handle)) !== false) {
        // Ensure the row has at least two columns
        if (count($row) < 2) {
            error_log("CSV row has insufficient columns: " . json_encode($row));
            continue;
        }
        $csvDocument = trim($row[0]);
        $csvTemplate = trim($row[1]);

        error_log("Comparing CSV document: '$csvDocument' with target: '$target'");
        if ($csvDocument === $target) {
            fclose($handle);
            $templatePath = rtrim($templatesDir, '/') . '/' . $csvTemplate;
            error_log("Found match. Template path: '$templatePath'");

            if (file_exists($templatePath)) {
                return $templatePath;
            } else {
                error_log("Template file does not exist at path: '$templatePath'");
                return false;
            }
        }
    }

    fclose($handle);
    error_log("No matching template found for document: '$target'");
    return false;
}

function generateDocumentAgain($templateFile, $contentFile, $outputFile) {
    // Example: Using Pandoc or LaTeX command
    $command = "pdflatex -interaction=nonstopmode -output-directory=" . dirname($outputFile) . " " . escapeshellarg($templateFile);
    
    exec($command, $output, $return_var);
    
    return ($return_var === 0) ? true : false;
}


function importTemplate()
{
    $targetDir = 'templates/';
    
    // Ensure the directory exists
    if (!is_dir($targetDir)) {
        mkdir($targetDir, 0777, true);
    }

    // Validate file upload
    if (!isset($_FILES['template']) || $_FILES['template']['error'] !== UPLOAD_ERR_OK) {
        echo json_encode(["success" => false, "error" => "File upload failed"]);
        exit;
    }

    $targetFile = $targetDir . basename($_FILES['template']['name']);
    
    if (move_uploaded_file($_FILES['template']['tmp_name'], $targetFile)) {
        echo json_encode(["success" => true, "message" => "Template uploaded successfully"]);
    } else {
        echo json_encode(["success" => false, "error" => "File move failed"]);
    }
}

function exportTemplate()
{
    if (!isset($_GET['name'])) {
        echo json_encode(["success" => false, "error" => "No template name provided"]);
        return;
    }

    $file = 'templates/' . basename($_GET['name']);
    
    if (file_exists($file)) {
        header('Content-Type: application/octet-stream');
        header('Content-Disposition: attachment; filename="' . basename($file) . '"');
        readfile($file);
        exit;
    } else {
        echo json_encode(["success" => false, "error" => "Template not found"]);
    }
}

function deleteTemplate()
{
    if (!isset($_POST['name'])) {
        echo json_encode(["success" => false, "error" => "No template name provided"]);
        return;
    }

    $file = 'templates/' . basename($_POST['name']);
    
    if (file_exists($file) && unlink($file)) {
        echo json_encode(["success" => true, "message" => "Template deleted successfully"]);
    } else {
        echo json_encode(["success" => false, "error" => "Failed to delete template"]);
    }
}

function getTemplates()
{
    $dir = 'templates/';
    if (!is_dir($dir)) {
        echo json_encode([]);
        return;
    }

    $files = array_diff(scandir($dir), ['.', '..']);
    echo json_encode(array_values($files));
}

function generateDocument()
{
    $template = $_POST['template'] ?? '';
    $date = $_POST['date'] ?? '';
    $place = $_POST['place'] ?? '';
    $content = $_POST['content'] ?? '';

    if (!$template || !$date || !$place || !$content || !isset($_FILES['templateFile'])) {
        echo json_encode(["success" => false, "error" => "Missing required fields"]);
        return;
    }

    $documentId = uniqid("doc_") . '_' . $date . '_' . $place . '_' . $template;

    $documentDir = "documents/";
    $pdfDir = "generated_pdfs/";

    if (!is_dir($documentDir)) {
        mkdir($documentDir, 0777, true);
    }
    if (!is_dir($pdfDir)) {
        mkdir($pdfDir, 0777, true);
    }

    // // Save plain text document
    // $txtFilePath = "{$documentDir}{$documentId}.txt";
    // file_put_contents($txtFilePath, "Template: $template\nDate: $date\nPlace: $place\nContent:\n$content");

    // Process uploaded template file
    $uploadedTemplatePath = $_FILES['templateFile']['tmp_name'];
    $latexFilePath = "{$documentDir}{$documentId}.tex";


    $csv_file = 'templates.csv';
    $csv_data = [$documentId, $template, $date, $place, date('Y-m-d H:i:s')];

    if (!file_exists($csv_file)) {
        $fp = fopen($csv_file, 'w'); // 'w' creates the file if it doesn't exist
        if ($fp) {
            fputcsv($fp, ['DocumentID', 'Template', 'Date', 'Place', 'Timestamp']); // Add headers
            fclose($fp);
        } else {
            echo json_encode(["success" => false, "error" => "Failed to create CSV file"]);
            return;
        }
    }

    $fp = fopen($csv_file, 'a');
    fputcsv($fp, $csv_data);
    fclose($fp);

    // Read and replace placeholders in template
    $latexContent = file_get_contents($uploadedTemplatePath);
    $latexContent = str_replace(['{{DATE}}', '{{PLACE}}', '{{CONTENT}}'], [$date, $place, $content], $latexContent);
    file_put_contents($latexFilePath, $latexContent);

    // Generate PDF using FPDF
    $pdfFilePath = "{$pdfDir}{$documentId}.pdf";
    $pdf = new FPDF();
    $pdf->AddPage();
    $pdf->SetFont('Arial', 'B', 16);
    $pdf->Cell(0, 10, "Generated Document", 0, 1, 'C');

    $pdf->SetFont('Arial', '', 12);
    $pdf->Ln(5);
    //$pdf->Cell(0, 10, "Template: $template", 0, 1);
    $pdf->Cell(0, 10, "$date", 0, 1);
    $pdf->Cell(0, 10, "$place", 0, 1);
    $pdf->Ln(5);

    $pdf->SetFont('Arial', '', 11);
    $pdf->MultiCell(0, 8, "\n$content");

    $pdf->Output($pdfFilePath, 'F');

    echo json_encode([
        "success" => true,
        "documentId" => $documentId,
        "pdf_url" => "http://localhost:8000/{$pdfFilePath}"
    ]);
}



function searchDocuments()
{
    $query = $_POST['query'] ?? '';
    $date = $_POST['date'] ?? '';
    $place = $_POST['place'] ?? '';

    $csv_file = 'templates.csv';
    if (!file_exists($csv_file)) {
        echo json_encode([]);
        return;
    }

    $results = [];
    $fp = fopen($csv_file, 'r');

    while (($row = fgetcsv($fp)) !== false) {
        list($doc_id, $template, $doc_date, $doc_place, $timestamp) = $row;
        
        // Check if any search condition matches
        if (
            (!$query || stripos($filename, $query) !== false || stripos($template, $query) !== false) &&
            (!$date || $doc_date == $date) &&
            (!$place || stripos($doc_place, $place) !== false)
        ) {
            $results[] = [
                "documentId" => $doc_id,
                "filename" => $filename,
                "template" => $template,
                "date" => $doc_date,
                "place" => $doc_place,
                "timestamp" => $timestamp
            ];
        }
    }

    fclose($fp);
    echo json_encode($results);

}
