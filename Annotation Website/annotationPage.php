<?php
// Files used
define('DATA_FILE', 'combined_data.json');
// Define the threshold for needing multiple annotations or checking ambiguity
define('ANNOTATION_THRESHOLD', 3);

// Function to load data from the JSON file
function load_data()
{
    if (file_exists(DATA_FILE)) {
        $json_content = file_get_contents(DATA_FILE);
        // Add basic JSON decode error check
        $data = json_decode($json_content, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
             error_log("Error decoding JSON from " . DATA_FILE . ": " . json_last_error_msg());
             return []; // Return empty on decode error
        }
        return $data ?: []; // Return empty array if json_decode returns null or false
    }
    return [];
}

// Helper function to check if a user has annotated a specific entry
function hasUserAnnotated($entry, $user_id) {
    // If no user ID is provided, they haven't annotated it in a trackable way
    if (!$user_id) {
        return false;
    }
    // Check if user_votes exist and is an array
    if (!isset($entry['user_votes']) || !is_array($entry['user_votes'])) {
        return false;
    }
    // Loop through votes to find the user_id
    foreach ($entry['user_votes'] as $vote) {
        if (isset($vote['user_id']) && $vote['user_id'] === $user_id) {
            return true; // User found
        }
    }
    return false; // User not found
}

// Helper function to check if an entry lacks a clear majority vote AT OR ABOVE the threshold
function isAmbiguous($entry, $total) {
     // Ambiguity check is typically relevant at or above the threshold
     if ($total < ANNOTATION_THRESHOLD) {
         return false; // Not enough votes to be considered ambiguous in this context
     }

     $pos = isset($entry['positive']) ? $entry['positive'] : 0;
     $neg = isset($entry['negative']) ? $entry['negative'] : 0;
     $neu = isset($entry['neutral']) ? $entry['neutral'] : 0;
     $ma  = isset($entry['ma nafx']) ? $entry['ma nafx'] : 0;

     // Check if any ONE category is strictly greater than ALL others
     $has_clear_majority = (
         ($pos > $neg && $pos > $neu && $pos > $ma) ||
         ($neg > $pos && $neg > $neu && $neg > $ma) ||
         ($neu > $pos && $neu > $neg && $neu > $ma) ||
         ($ma > $pos && $ma > $neg && $ma > $neu) // Added 'ma nafx' to majority check
     );

     // It's ambiguous if it does NOT have a clear majority
     return !$has_clear_majority;
}


// Main logic for sentence selection
function get_sentences_to_annotate()
{
    $all_data = load_data();
    // Handle case where data loading failed or file is empty
    if (empty($all_data)) {
         return [
            'sentences' => [],
            'total_displayed' => 0,
            'progress_percentage' => 0,
            'annotated_count' => 0,
            'total_sentences' => 0,
            'no_more_sentences' => true
        ];
    }

    $user_id = isset($_COOKIE['user_id']) ? $_COOKIE['user_id'] : null;

    $candidate_entries = []; // Array to hold entries suitable for the current user

    // Iterate through all entries to find candidates for *this* user
    foreach ($all_data as $entry) {
        // CRITERIA 1: User must NOT have annotated this sentence previously
        if ($user_id && hasUserAnnotated($entry, $user_id)) {
            continue; // Skip this sentence, user already voted
        }

        // Calculate total annotations for this entry
        $pos = isset($entry['positive']) ? $entry['positive'] : 0;
        $neg = isset($entry['negative']) ? $entry['negative'] : 0;
        $neu = isset($entry['neutral']) ? $entry['neutral'] : 0;
        $ma  = isset($entry['ma nafx']) ? $entry['ma nafx'] : 0;
        $entry_total = $pos + $neg + $neu + $ma;

        // CRITERIA 2: Sentence should be shown if EITHER:
        // a) It has fewer than the threshold number of annotations OR
        // b) It has reached the threshold but is ambiguous (lacks a clear majority)
        if ($entry_total < ANNOTATION_THRESHOLD) {
            $candidate_entries[] = $entry; // Needs more votes regardless of ambiguity
        } elseif (isAmbiguous($entry, $entry_total)) {
            // Has enough votes, but no clear winner - show to users who haven't voted yet
            $candidate_entries[] = $entry;
        }
        // Implicit else: If entry_total >= threshold AND !isAmbiguous(), it's skipped (already resolved)
    }

    // MODIFICATION: Group entries by number of annotations and then randomize within each group
    // First, group entries by their annotation count
    $grouped_entries = [];
    foreach ($candidate_entries as $entry) {
        $total = (isset($entry['positive']) ? $entry['positive'] : 0) +
                (isset($entry['negative']) ? $entry['negative'] : 0) +
                (isset($entry['neutral']) ? $entry['neutral'] : 0) +
                (isset($entry['ma nafx']) ? $entry['ma nafx'] : 0);
        
        // Create array for this count if it doesn't exist
        if (!isset($grouped_entries[$total])) {
            $grouped_entries[$total] = [];
        }
        
        // Add entry to its count group
        $grouped_entries[$total][] = $entry;
    }
    
    // Sort the groups by key (annotation count) in descending order
    krsort($grouped_entries);
    
    // Shuffle each group internally for randomization
    foreach ($grouped_entries as &$group) {
        shuffle($group);
    }
    
    // Flatten the array while maintaining the priority order
    $prioritized_entries = [];
    foreach ($grouped_entries as $group) {
        foreach ($group as $entry) {
            $prioritized_entries[] = $entry;
        }
    }

    // Select up to 3 sentences from the prioritized list
    // Ensure we're selecting unique entries by tracking their content
    $selected_sentences = [];
    $selected_content_tracker = [];
    $i = 0;
    $max_to_select = min(3, count($prioritized_entries));
    
    while (count($selected_sentences) < $max_to_select && $i < count($prioritized_entries)) {
        $entry = $prioritized_entries[$i];
        $content = isset($entry['content']) ? $entry['content'] : '';
        
        // Check if we already have this content in our selection
        if (!empty($content) && !in_array($content, $selected_content_tracker)) {
            $selected_sentences[] = $entry;
            $selected_content_tracker[] = $content;
        }
        $i++;
    }
    
    $selected_sentences_content = [];

    // Extract the content
    foreach ($selected_sentences as $entry) {
        if (isset($entry['content'])) {
            $selected_sentences_content[] = $entry['content'];
        } else {
            error_log("Warning: Entry is missing 'content' field.");
        }
    }
    
    // Ensure we have unique sentences
    $selected_sentences_content = array_unique($selected_sentences_content);

    // Calculate overall progress details (using the original $all_data)
    $total_entries = count($all_data);
    $annotated_count = 0;
    foreach ($all_data as $entry) {
        $entry_total = (isset($entry['positive']) ? $entry['positive'] : 0) +
                       (isset($entry['negative']) ? $entry['negative'] : 0) +
                       (isset($entry['neutral']) ? $entry['neutral'] : 0) +
                       (isset($entry['ma nafx']) ? $entry['ma nafx'] : 0);
        if ($entry_total > 0) {
            $annotated_count++;
        }
    }
    $progress_percentage = ($total_entries > 0) ? round(($annotated_count / $total_entries) * 100) : 0;

    // Return the results
    return [
        'sentences' => $selected_sentences_content,
        'total_displayed' => count($selected_sentences_content), // How many are shown now
        'progress_percentage' => $progress_percentage,           // Overall progress
        'annotated_count' => $annotated_count,                 // Overall annotated sentences
        'total_sentences' => $total_entries,                   // Overall total sentences
        'no_more_sentences' => empty($selected_sentences_content) // Flag if nothing suitable was found for this user
    ];
}

// --- Call the function ---
$data = get_sentences_to_annotate();

?>
<!DOCTYPE html>
<html lang="en">

<head class="annotation-page">
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SentiMalti</title>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap">
    <link rel="stylesheet" href="static/css/styles.css">
    <style>
        .logo {
            text-decoration: none;
            color: #000;
        }
    </style>
</head>

<body class="annotation-page">
    <header class="home-page">
        <img src="UM Logo.png" alt="L-Università ta' Malta" class="logo">
        <div class="faculty-badge">Fakultà tal-ICT</div>
    </header>

    <main>
        <div class="content">
            <h1 class="main-title">Annotazzjoni tas-Sentenzi</h1>

            <?php if ($data['no_more_sentences']): ?>
                <p>Ma fadalx sentenzi x'tannota. Grazzi għall-kontribuzzjonijiet tiegħek!</p>
            <?php else: ?>
                <p style="margin-bottom: 1.5rem; line-height: 1.6;">Inti tista' tannota kemm trid sentenzi. Meta trid, tista' tagħfas il-buttuna "Ieqaf" biex ittemm din is-sezzjoni.<br>
                    Jekk tkun trid li tbiddel is-sentenzi li hawn hawn taħt, tista' tagħfas il-buttuna "Refresh" biex ittik sentenzi ġodda.</p>

                <div class="instruction-wrapper" style="display: flex; align-items: center; gap: 1rem;">
                    <div class="instructions-box">
                        Aqra kull sentenza u agħżel is-sentiment li jiddeskrivi l-aħjar:<br>
                        - <strong>Pożittiv</strong>: Is-sentenza tesprimi ferħ, sodisfazzjon, jew esperjenza tajba.<br>
                        <p style="text-indent: 1.5em; font-style: italic;">"Il-prodott kien tassew tajjeb u wasal fil-ħin perfett!"<br></p>
                        - <strong>Newtrali</strong>: Is-sentenza hija fattwali, bilanċjata, jew nieqsa minn emozzjoni qawwija.<br>
                        <p style="text-indent: 1.5em; font-style: italic;">"Il-ħanut jiftaħ fis-7 ta' filgħodu u jagħlaq fis-6 ta' filgħaxija."<br></p>
                        - <strong>Negattiv</strong>: Is-sentenza turi diżappunt, rabja, jew esperjenza ħażina.
                        <p style="text-indent: 1.5em; font-style: italic;">"Kont diżappuntat ħafna għax is-servizz kien ħażin ħafna."<br></p>
                    </div>
                    <div class="instruction-buttons" style="display: flex; flex-direction: row; gap: 6rem;">
                        <button onclick="window.location.href='finishPage.php'" class="btn" style="color: black;">Ieqaf</button>
                        <button onclick="window.location.reload()" class="btn" style="color: black;">Refresh</button>
                    </div>
                </div>
                <div id="sentences-container">
                    <?php foreach ($data['sentences'] as $index => $sentence): ?>
                        <div class="sentence-box" data-index="<?php echo $index; ?>">
                            <p class="sentence"><?php echo htmlspecialchars($sentence); ?></p>
                            <div class="annotation-buttons" style="display: flex; justify-content: center; align-items: center; gap: 1rem;">
                                <div class="btn-group" style="display: flex; gap: 1rem;">
                                    <button onclick="annotate(this, 'positive')" class="btn green">Pożittiv</button>
                                    <button onclick="annotate(this, 'neutral')" class="btn yellow">Newtrali</button>
                                    <button onclick="annotate(this, 'negative')" class="btn red">Negattiv</button>
                                </div>
                                <button onclick="annotate(this, 'Ma nafx')" class="btn" style="margin-left: 1rem; color: black;">Ma nafx</button>
                            </div>
                        </div>
                    <?php endforeach; ?>
                </div>
                <div id="progress-bar-container" data-total-sentences="<?php echo $data['total_displayed']; ?>">
                    <div role="progressbar" aria-valuenow="<?php echo $data['progress_percentage']; ?>" aria-valuemin="0" aria-valuemax="100">
                        <div style="width: 50%;"></div>
                    </div>
                </div>
                <p>Progress: <span id="progress-count">0</span> minn <?php echo $data['total_displayed']; ?> sentenzi annotati</p>
            <?php endif; ?>
        </div>
    </main>

    <footer>
        &copy; 2024/5 Proġett GAPT - SentiMalti
    </footer>

    <script src="static/js/script.js"></script>
</body>

</html>