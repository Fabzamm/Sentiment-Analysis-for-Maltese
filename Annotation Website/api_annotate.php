<?php
header('Content-Type: application/json');

// Files used
define('DATA_FILE', 'combined_data.json');

// Function to load data from the JSON file
function load_data() {
    if (file_exists(DATA_FILE)) {
        $json_content = file_get_contents(DATA_FILE);
        return json_decode($json_content, true);
    }
    return [];
}

// Function to save data to the JSON file
function save_data($data) {
    file_put_contents(DATA_FILE, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

// Function to save an annotation to the JSON file
function save_annotation($sentence, $sentiment, $user_id) {
    $data = load_data();
    $key = strtolower($sentiment);  // expected to be "positive", "negative", "neutral" or "ma nafx"
    $valid_keys = ['positive', 'neutral', 'negative', 'ma nafx'];
    $now = date('c'); // ISO 8601 date format
    
    foreach ($data as &$entry) {
        if ($entry['content'] === $sentence) {
            // Ensure all sentiment keys are present
            foreach ($valid_keys as $k) {
                if (!isset($entry[$k])) {
                    $entry[$k] = 0;
                }
            }
            // Increment the proper sentiment counter and update the timestamp
            $entry[$key]++;
            $entry['updated_at'] = $now;
            
            // Append the new vote into the user_votes array
            if (!isset($entry['user_votes'])) {
                $entry['user_votes'] = [];
            }
            
            $entry['user_votes'][] = [
                'user_id' => $user_id,
                'sentiment' => $key,
                'updated_time' => $now
            ];
            break;
        }
    }
    
    save_data($data);
}

// Check if request is POST and has JSON content
$is_post = $_SERVER['REQUEST_METHOD'] === 'POST';
$content_type = isset($_SERVER['CONTENT_TYPE']) ? $_SERVER['CONTENT_TYPE'] : '';
$is_json = strpos($content_type, 'application/json') !== false;

if ($is_post && $is_json) {
    // Get the JSON data from the request
    $json_str = file_get_contents('php://input');
    $data_req = json_decode($json_str, true);
    
    // Check if the user has a unique ID in their cookies
    $user_id = isset($_COOKIE['user_id']) ? $_COOKIE['user_id'] : '';
    if (empty($user_id)) {
        $user_id = uniqid('user_', true);
        // Set the cookie for 1 year
        setcookie('user_id', $user_id, time() + (365 * 24 * 60 * 60), '/');
    }
    
    if (isset($data_req['sentence']) && isset($data_req['sentiment'])) {
        $sentence = $data_req['sentence'];
        $sentiment = $data_req['sentiment'];
        
        // Save annotation with the provided user_id
        save_annotation($sentence, $sentiment, $user_id);
        
        echo json_encode([
            'success' => true, 
            'message' => "Sentence \"$sentence\" annotated as $sentiment"
        ]);
    } else {
        http_response_code(400);
        echo json_encode([
            'success' => false, 
            'message' => 'Missing required fields'
        ]);
    }
} else {
    http_response_code(405);
    echo json_encode([
        'success' => false, 
        'message' => 'Method not allowed or incorrect content type'
    ]);
}
?>