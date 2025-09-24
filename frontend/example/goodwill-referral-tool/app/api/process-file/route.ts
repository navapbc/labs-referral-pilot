import { type NextRequest, NextResponse } from "next/server"
import { openai } from "@ai-sdk/openai"
import { generateText } from "ai"

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get("file") as File
    const filtersString = formData.get("filters") as string

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 })
    }

    const filters = JSON.parse(filtersString || "{}")

    // Convert file to base64 for OpenAI API
    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)

    let extractedText = ""

    // Handle different file types
    if (file.type === "application/pdf") {
      // For PDFs, we'll use OpenAI's vision API with a message about PDF processing
      const base64 = buffer.toString("base64")

      const { text } = await generateText({
        model: openai("gpt-4o"),
        messages: [
          {
            role: "user",
            content: [
              {
                type: "text",
                text: "This is a PDF intake form. Please extract all client information including name, age, address, income, family situation, housing status, employment, health conditions, disabilities, transportation needs, and any other relevant details that could help determine appropriate social services referrals. Format the information clearly and comprehensively. IMPORTANT: At the end of your response, include a citation noting that this analysis was performed by AI (ChatGPT/GPT-4) and should be reviewed by a human case worker for accuracy.",
              },
              {
                type: "image",
                image: `data:${file.type};base64,${base64}`,
              },
            ],
          },
        ],
      })

      extractedText = text
    } else if (file.type.startsWith("image/")) {
      // Handle image files
      const base64 = buffer.toString("base64")

      const { text } = await generateText({
        model: openai("gpt-4o"),
        messages: [
          {
            role: "user",
            content: [
              {
                type: "text",
                text: "This is an intake form image (could be handwritten or typed). Please extract all client information including name, age, address, income, family situation, housing status, employment, health conditions, disabilities, transportation needs, and any other relevant details that could help determine appropriate social services referrals. Format the information clearly and comprehensively. IMPORTANT: At the end of your response, include a citation noting that this analysis was performed by AI (ChatGPT/GPT-4) and should be reviewed by a human case worker for accuracy.",
              },
              {
                type: "image",
                image: `data:${file.type};base64,${base64}`,
              },
            ],
          },
        ],
      })

      extractedText = text
    } else {
      return NextResponse.json({ error: "Unsupported file type" }, { status: 400 })
    }

    return NextResponse.json({
      extractedText,
      filters,
    })
  } catch (error) {
    console.error("Error processing file:", error)
    return NextResponse.json({ error: "Failed to process file" }, { status: 500 })
  }
}
