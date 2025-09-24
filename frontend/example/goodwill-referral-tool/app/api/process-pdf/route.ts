import { type NextRequest, NextResponse } from "next/server"
import { generateText } from "ai"
import { openai } from "@ai-sdk/openai"

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const pdfFile = formData.get("pdf") as File
    const filtersString = formData.get("filters") as string

    if (!pdfFile) {
      return NextResponse.json({ error: "No PDF file provided" }, { status: 400 })
    }

    const filters = JSON.parse(filtersString || "{}")

    // Convert PDF to base64 for processing
    const arrayBuffer = await pdfFile.arrayBuffer()
    const base64 = Buffer.from(arrayBuffer).toString("base64")

    // Use OpenAI to extract text and analyze the PDF
    const { text } = await generateText({
      model: openai("gpt-4o"),
      messages: [
        {
          role: "user",
          content: [
            {
              type: "text",
              text: `Please analyze this intake form PDF and extract key client information that would be relevant for generating social service referrals. Focus on:

1. Demographics (age, family size, location)
2. Current challenges and needs (housing, employment, healthcare, etc.)
3. Barriers to services (transportation, childcare, language, etc.)
4. Goals and priorities mentioned
5. Any specific circumstances or urgent needs

Please provide a comprehensive summary that captures the client's situation in a way that would help generate appropriate referrals. Format this as a clear, detailed description that could be used as input for a referral system.

Applied filters:
- Resource categories: ${filters.categories?.join(", ") || "All categories"}
- County: ${filters.county || "All counties"}
- City: ${filters.city || "Not specified"}
- ZIP Code: ${filters.zipCode || "Not specified"}

Please incorporate these location and category preferences into your analysis.`,
            },
            {
              type: "image",
              image: `data:application/pdf;base64,${base64}`,
            },
          ],
        },
      ],
      maxTokens: 1000,
    })

    return NextResponse.json({
      extractedText: text,
      success: true,
    })
  } catch (error) {
    console.error("Error processing PDF:", error)
    return NextResponse.json({ error: "Failed to process PDF" }, { status: 500 })
  }
}
