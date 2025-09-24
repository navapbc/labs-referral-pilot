import { generateText } from "ai"
import { openai } from "@ai-sdk/openai"

export async function POST(request: Request) {
  try {
    const { clientDescription, conversationHistory = [], isFollowUp = false } = await request.json()

    if (!clientDescription) {
      return Response.json({ error: "Client description is required" }, { status: 400 })
    }

    let contextPrompt = ""
    if (isFollowUp && conversationHistory.length > 0) {
      contextPrompt = "\n\nPrevious conversation context:\n"
      conversationHistory.forEach((entry: any, index: number) => {
        contextPrompt += `\nQ${index + 1}: ${entry.prompt}\nA${index + 1}: ${entry.response.question} - ${entry.response.summary}\n`
      })
      contextPrompt += "\nCurrent follow-up question: "
    }

    const prompt = isFollowUp
      ? `You are a social services case manager AI assistant for Goodwill Central Texas. This is a follow-up question based on previous conversation.

${contextPrompt}${clientDescription}

Provide a helpful, conversational response that directly answers the follow-up question. You can respond in any format that's most appropriate - it could be a simple explanation, additional resources, clarification, or guidance. Be natural and helpful.

Use markdown formatting for better readability:
- Use **bold** for emphasis
- Use bullet points with * for lists
- Use ## for section headers
- Use ### for subsection headers

Format the response as JSON with this structure:
{
  "question": "Restate the follow-up question clearly",
  "summary": "Brief summary of your response",
  "content": "Your full response content with markdown formatting"
}

IMPORTANT: Return ONLY the JSON object, no markdown formatting or code blocks.`
      : `You are a social services case manager AI assistant for Goodwill Central Texas. Based on the client description provided, generate a helpful referral response that includes:

1. A clear question summarizing the client's main needs
2. A list of 3-4 specific local resources in Central Texas (prioritize Goodwill services when applicable)
3. 3-4 suggested follow-up questions that focus on getting more details about the specific resources provided

For each resource, include:
- Organization name and service type
- Brief description with key details (eligibility, schedule, cost)
- "Why it fits" explanation
- Contact information (phone, address, website)
- Source reference with SPECIFIC detailed URLs

CRITICAL: For source references and contact websites, provide SPECIFIC detailed URLs that go directly to the program or service page, NOT the organization's homepage. Examples:
- For Lyft Up rideshare assistance: https://www.lyft.com/lyftup/programs (NOT just lyft.com)
- For SNAP benefits: https://www.hhs.texas.gov/services/food/snap (NOT just hhs.texas.gov)
- For Goodwill job training: https://www.goodwillcentraltexas.org/job-training-programs (NOT just goodwillcentraltexas.org)
- For Austin Energy assistance: https://austinenergy.com/ae/residential/your-bill/help-paying-your-bill/customer-assistance-program (NOT just austinenergy.com)

Always find and use the most specific URL that directly describes the exact service or program being referenced.

For suggested follow-ups, create questions that ask for more details about HOW TO USE or ACCESS the specific resources you provided. Examples:
- "Write a guide to applying for reduced fare" (for transportation resources)
- "Explain the application process for food assistance" (for food resources)
- "What are the eligibility requirements for this job training program?" (for employment resources)
- "How do I schedule an appointment at this location?" (for service resources)

Format the response as JSON with this structure:
{
  "question": "What resources can help...",
  "summary": "Brief summary of what was found",
  "resources": [
    {
      "number": 1,
      "title": "Organization Name",
      "service": "Service type",
      "description": "Description with key details",
      "whyItFits": "Why this resource matches the client's needs",
      "contact": "Contact information with specific detailed URL",
      "source": "Source reference with specific detailed URL",
      "badge": "specific-program-page.com (not homepage)"
    }
  ],
  "suggestedFollowUps": [
    "How-to question about accessing the first resource",
    "Process question about applying for the second resource",
    "Eligibility or requirement question about the third resource"
  ]
}

IMPORTANT: Return ONLY the JSON object, no markdown formatting or code blocks.

Client description: ${clientDescription}`

    const { text } = await generateText({
      model: openai("gpt-4o"),
      prompt,
      temperature: 0.7,
    })

    let cleanedText = text.trim()

    // Remove markdown code blocks if present
    if (cleanedText.startsWith("```json")) {
      cleanedText = cleanedText.replace(/^```json\s*/, "").replace(/\s*```$/, "")
    } else if (cleanedText.startsWith("```")) {
      cleanedText = cleanedText.replace(/^```\s*/, "").replace(/\s*```$/, "")
    }

    cleanedText = cleanedText.trim()

    let referralData
    try {
      referralData = JSON.parse(cleanedText)
    } catch (parseError) {
      console.error("JSON parsing failed:", parseError)
      console.error("Raw response:", text)
      console.error("Cleaned response:", cleanedText)

      // Return a fallback response
      return Response.json(
        {
          error: "Failed to parse AI response",
          rawResponse: text.substring(0, 500), // First 500 chars for debugging
        },
        { status: 500 },
      )
    }

    return Response.json(referralData)
  } catch (error) {
    console.error("Error generating referrals:", error)
    return Response.json({ error: "Failed to generate referrals" }, { status: 500 })
  }
}
