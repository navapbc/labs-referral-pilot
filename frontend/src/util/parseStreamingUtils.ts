/**
 * Common utilities for parsing streaming JSON responses
 */

/**
 * Unescapes JSON string escape sequences
 */
export function unescapeJSON(str: string): string {
  return str
    .replace(/\\n/g, "\n")
    .replace(/\\r/g, "\r")
    .replace(/\\t/g, "\t")
    .replace(/\\"/g, '"')
    .replace(/\\\\/g, "\\");
}

/**
 * Fixes unescaped control characters in JSON string values
 * This handles cases where the LLM returns JSON with literal newlines, tabs, etc.
 */
export function fixJsonControlCharacters(jsonString: string): string {
  let inString = false;
  let result = "";
  let prevChar = "";

  for (let i = 0; i < jsonString.length; i++) {
    const currentChar = jsonString[i];

    // Toggle string state when we hit an unescaped quote
    if (currentChar === '"' && prevChar !== "\\") {
      inString = !inString;
      result += currentChar;
    } else if (inString) {
      // Inside a string value - escape control characters
      if (currentChar === "\n") {
        result += "\\n";
      } else if (currentChar === "\r") {
        result += "\\r";
      } else if (currentChar === "\t") {
        result += "\\t";
      } else if (currentChar === "\b") {
        result += "\\b";
      } else if (currentChar === "\f") {
        result += "\\f";
      } else {
        result += currentChar;
      }
    } else {
      // Outside string values - keep as is
      result += currentChar;
    }

    prevChar = currentChar;
  }

  return result;
}

/**
 * Extracts a field value from partial JSON, handling incomplete strings
 * Pattern matches escaped characters: (?:[^"\\]|\\.)*
 * - [^"\\] matches any char except quote or backslash
 * - \\. matches backslash followed by any char (handles \", \n, etc)
 */
export function extractField(
  jsonStr: string,
  fieldName: string,
): string | undefined {
  // Try complete field first (with closing quote)
  const completeMatch = jsonStr.match(
    new RegExp(`"${fieldName}"\\s*:\\s*"((?:[^"\\\\]|\\\\.)*)"`),
  );
  if (completeMatch) {
    return unescapeJSON(completeMatch[1]);
  }

  // Try incomplete field (no closing quote yet)
  const incompleteMatch = jsonStr.match(
    new RegExp(`"${fieldName}"\\s*:\\s*"((?:[^"\\\\]|\\\\.)*)`),
  );
  if (incompleteMatch) {
    return unescapeJSON(incompleteMatch[1]);
  }

  return undefined;
}

/**
 * Extracts array items from partial JSON
 * Handles both complete and incomplete array strings
 */
export function extractArrayField(
  jsonStr: string,
  fieldName: string,
): string[] {
  const result: string[] = [];

  // Try to match the entire array field
  // Using [\s\S] instead of . to match any character including newlines (compatible with ES2017)
  const arrayPattern = new RegExp(
    `"${fieldName}"\\s*:\\s*\\[([\\s\\S]*?)(?:\\]|$)`,
  );
  const arrayMatch = jsonStr.match(arrayPattern);

  if (!arrayMatch) {
    return result;
  }

  const arrayContent = arrayMatch[1];

  // Extract individual complete string items from the array.
  // This global pattern (/.../g) is used with exec() in a loop to find all
  // complete items whose content may include escaped quotes and other escapes.
  const itemPattern = /"((?:[^"\\]|\\.)*)"/g;
  let itemMatch;

  while ((itemMatch = itemPattern.exec(arrayContent)) !== null) {
    result.push(unescapeJSON(itemMatch[1]));
  }

  // Check for incomplete last item (string without closing quote)
  const incompleteItemPattern = /"((?:[^"\\]|\\.)*?)$/;
  const incompleteMatch = arrayContent.match(incompleteItemPattern);
  if (incompleteMatch && incompleteMatch[1]) {
    // Only add if it's not already captured (avoid duplicates)
    const unescaped = unescapeJSON(incompleteMatch[1]);
    if (!result.includes(unescaped)) {
      result.push(unescaped);
    }
  }

  return result;
}
