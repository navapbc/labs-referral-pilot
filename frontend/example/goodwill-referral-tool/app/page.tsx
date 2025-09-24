"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  Search,
  MapPin,
  FileText,
  Upload,
  Sparkles,
  Printer,
  CheckCircle,
  Copy,
  MessageCircle,
  Heart,
  Briefcase,
  Home,
  Utensils,
  Car,
  Stethoscope,
  Baby,
  DollarSign,
  GraduationCap,
  Scale,
  Shield,
  Accessibility,
  Flag,
  Menu,
  Grid3X3,
  ChevronDown,
  Star,
  UserPlus,
  Settings,
  ClipboardList,
  ArrowLeft,
  MoreHorizontal,
  Plus,
  RotateCcw,
  Building,
  Users,
  Filter,
  Eye,
  RefreshCw,
} from "lucide-react"

interface Resource {
  number: number
  title: string
  service: string
  description: string
  whyItFits: string
  contact: string
  source: string
  badge: string
}

interface ReferralResponse {
  question: string
  summary: string
  resources?: Resource[]
  suggestedFollowUps?: string[]
  content?: string
}

const resourceCategories = [
  { id: "employment", label: "Employment & Job Training", icon: Briefcase, color: "bg-blue-100 text-blue-800" },
  { id: "housing", label: "Housing & Shelter", icon: Home, color: "bg-green-100 text-green-800" },
  { id: "food", label: "Food Assistance", icon: Utensils, color: "bg-orange-100 text-orange-800" },
  { id: "transportation", label: "Transportation", icon: Car, color: "bg-purple-100 text-purple-800" },
  { id: "healthcare", label: "Healthcare & Mental Health", icon: Stethoscope, color: "bg-red-100 text-red-800" },
  { id: "childcare", label: "Childcare", icon: Baby, color: "bg-pink-100 text-pink-800" },
  { id: "financial", label: "Financial Assistance", icon: DollarSign, color: "bg-yellow-100 text-yellow-800" },
  { id: "education", label: "Education & GED", icon: GraduationCap, color: "bg-indigo-100 text-indigo-800" },
  { id: "legal", label: "Legal Services", icon: Scale, color: "bg-gray-100 text-gray-800" },
  { id: "substance", label: "Substance Abuse Treatment", icon: Shield, color: "bg-teal-100 text-teal-800" },
  { id: "disability", label: "Disability Services", icon: Accessibility, color: "bg-cyan-100 text-cyan-800" },
  { id: "veterans", label: "Veterans Services", icon: Flag, color: "bg-emerald-100 text-emerald-800" },
]

function parseMarkdownToHTML(content: string): string {
  if (!content) return ""

  let html = content

  // Convert headers (must be at start of line)
  html = html.replace(/^### (.+)$/gm, '<h3 class="text-lg font-semibold mb-2 text-slate-800">$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2 class="text-xl font-semibold mb-3 text-slate-800">$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold mb-4 text-slate-900">$1</h1>')

  // Convert bold text
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-slate-900">$1</strong>')

  // Convert italic text
  html = html.replace(/\*(.+?)\*/g, '<em class="italic">$1</em>')

  // Convert links
  html = html.replace(
    /\[(.+?)\]$$(.+?)$$/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">$1</a>',
  )

  // Convert bullet points (lines starting with * or -)
  html = html.replace(/^[*-] (.+)$/gm, '<li class="mb-1 leading-relaxed">$1</li>')

  // Convert numbered lists (lines starting with number.)
  html = html.replace(/^\d+\. (.+)$/gm, '<li class="mb-1 leading-relaxed">$1</li>')

  // Wrap consecutive <li> elements in <ul> or <ol>
  html = html.replace(/(<li[^>]*>.*?<\/li>\s*)+/gs, (match) => {
    return `<ul class="list-disc ml-6 mb-4 space-y-1">${match}</ul>`
  })

  // Convert double line breaks to paragraphs
  html = html.replace(/\n\n/g, '</p><p class="mb-3 leading-relaxed">')

  // Wrap in paragraph tags if not already wrapped
  if (!html.includes("<p>") && !html.includes("<h") && !html.includes("<ul>")) {
    html = `<p class="mb-3 leading-relaxed">${html}</p>`
  } else if (!html.startsWith("<")) {
    html = `<p class="mb-3 leading-relaxed">${html}`
  }

  return html
}

export default function ReferralTool() {
  const [clientDescription, setClientDescription] = useState("")
  const [showResults, setShowResults] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [caseNotes, setCaseNotes] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [processingTime, setProcessingTime] = useState("")
  const [followUpPrompt, setFollowUpPrompt] = useState("")
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [zipCode, setZipCode] = useState("")
  const [locationText, setLocationText] = useState("")
  const [activeTab, setActiveTab] = useState("text-summary")
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [isProcessingPDF, setIsProcessingPDF] = useState(false)
  const [pdfAnalysisResult, setPdfAnalysisResult] = useState<string>("")
  const [conversationHistory, setConversationHistory] = useState<
    Array<{
      prompt: string
      response: ReferralResponse
      timestamp: string
    }>
  >([])

  const [selectedResourceTypes, setSelectedResourceTypes] = useState<string[]>([])

  const mockHistory = [
    {
      id: 1,
      clientName: "Sarah Johnson",
      searchQuery: "Housing assistance for single mother with two children",
      date: "2024-01-15",
      status: "Completed",
      resourceTypes: ["Housing & Shelter", "Financial Assistance"],
      providerTypes: ["Government", "Community"],
      resultsCount: 8,
    },
    {
      id: 2,
      clientName: "Michael Rodriguez",
      searchQuery: "Employment training for veteran with PTSD",
      date: "2024-01-12",
      status: "Pending Follow-up",
      resourceTypes: ["Employment & Job Training", "Healthcare & Mental Health", "Veterans Services"],
      providerTypes: ["Government", "Goodwill Internal"],
      resultsCount: 12,
    },
    {
      id: 3,
      clientName: "Lisa Chen",
      searchQuery: "Childcare assistance for working parent",
      date: "2024-01-10",
      status: "Completed",
      resourceTypes: ["Childcare", "Financial Assistance"],
      providerTypes: ["Community", "Government"],
      resultsCount: 6,
    },
    {
      id: 4,
      clientName: "Robert Williams",
      searchQuery: "Substance abuse treatment and legal services",
      date: "2024-01-08",
      status: "In Progress",
      resourceTypes: ["Substance Abuse Treatment", "Legal Services"],
      providerTypes: ["Government", "Community"],
      resultsCount: 15,
    },
    {
      id: 5,
      clientName: "Maria Garcia",
      searchQuery: "Food assistance and transportation for elderly client",
      date: "2024-01-05",
      status: "Completed",
      resourceTypes: ["Food Assistance", "Transportation"],
      providerTypes: ["Community", "Government"],
      resultsCount: 9,
    },
  ]

  const handlePrintChatThread = () => {
    const printWindow = window.open("", "_blank")
    if (!printWindow) return

    const printContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Goodwill Central Texas - Referral Report</title>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              line-height: 1.6;
              color: #333;
              max-width: 800px;
              margin: 0 auto;
              padding: 20px;
            }
            .header {
              text-align: center;
              border-bottom: 2px solid #2563eb;
              padding-bottom: 15px;
              margin-bottom: 20px;
            }
            .header h1 {
              color: #2563eb;
              margin: 0;
              font-size: 24px;
            }
            .header p {
              margin: 3px 0 0 0;
              color: #666;
            }
            .exchange {
              margin-bottom: 25px;
              page-break-inside: avoid;
            }
            .question {
              background: #f8fafc;
              padding: 12px;
              border-radius: 8px;
              border-left: 4px solid #2563eb;
              margin-bottom: 12px;
            }
            .question h2 {
              margin: 0;
              font-size: 18px;
              color: #1e293b;
            }
            .summary {
              margin-bottom: 15px;
              font-weight: 500;
            }
            .resource {
              margin-bottom: 15px;
              padding: 12px;
              border: 1px solid #e2e8f0;
              border-radius: 6px;
            }
            .resource-header {
              display: flex;
              align-items: flex-start;
              gap: 10px;
              margin-bottom: 8px;
            }
            .resource-number {
              background: #2563eb;
              color: white;
              width: 24px;
              height: 24px;
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 14px;
              font-weight: bold;
              flex-shrink: 0;
            }
            .resource-title {
              font-weight: bold;
              color: #1e293b;
            }
            .resource-detail {
              margin: 6px 0;
              color: #475569;
            }
            .resource-contact {
              color: #1e293b;
            }
            .resource-source {
              color: #64748b;
              font-size: 14px;
            }
            .timestamp {
              text-align: center;
              color: #64748b;
              font-size: 14px;
              margin-top: 20px;
              padding-top: 15px;
              border-top: 1px solid #e2e8f0;
            }
            @media print {
              body { 
                margin: 0; 
                padding: 15px;
              }
              .header {
                padding-bottom: 10px;
                margin-bottom: 15px;
              }
              .exchange { 
                page-break-inside: avoid;
                margin-bottom: 20px;
              }
            }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>Goodwill Central Texas</h1>
            <p>GenAI Referral Tool - Client Referral Report</p>
            <p>Generated on ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}</p>
          </div>
          
          ${conversationHistory
            .map(
              (exchange, index) => `
            <div class="exchange">
              <div class="question">
                <h2>${exchange.response.question}</h2>
              </div>
              
              <div class="summary">
                ${exchange.response.summary}
              </div>
              
              ${
                exchange.response.resources
                  ? exchange.response.resources
                      .map(
                        (resource) => `
                <div class="resource">
                  <div class="resource-header">
                    <div class="resource-number">${resource.number}</div>
                    <div>
                      <div class="resource-title">${resource.title} - ${resource.service}</div>
                    </div>
                  </div>
                  <div class="resource-detail"><strong>Why it fits:</strong> ${resource.whyItFits}</div>
                  <div class="resource-detail resource-contact"><strong>Contact:</strong> ${resource.contact}</div>
                  <div class="resource-source"><strong>Source:</strong> ${resource.source} - ${resource.badge}</div>
                </div>
              `,
                      )
                      .join("")
                  : ""
              }
              
              ${
                exchange.response.content
                  ? `
                <div class="content">
                  ${exchange.response.content.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>")}
                </div>
              `
                  : ""
              }
            </div>
          `,
            )
            .join("")}
          
          <div class="timestamp">
            Report generated by Goodwill Central Texas GenAI Referral Tool
          </div>
        </body>
      </html>
    `

    printWindow.document.write(printContent)
    printWindow.document.close()
    printWindow.focus()
    printWindow.print()
  }

  const toggleCategory = (categoryId: string) => {
    setSelectedCategories((prev) =>
      prev.includes(categoryId) ? prev.filter((id) => id !== categoryId) : [...prev, categoryId],
    )
  }

  const clearAllFilters = () => {
    setSelectedCategories([])
    setZipCode("")
    setLocationText("")
    setSelectedResourceTypes([])
  }

  const toggleResourceType = (type: string) => {
    setSelectedResourceTypes((prev) => (prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]))
  }

  const handleGenerateReferrals = async (isFollowUp = false, customPrompt?: string) => {
    const prompt = customPrompt || (isFollowUp ? followUpPrompt : clientDescription)
    if (!prompt.trim()) return

    setIsLoading(true)
    const startTime = Date.now()

    try {
      const response = await fetch("/api/generate-referrals", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          clientDescription: prompt,
          conversationHistory: isFollowUp ? conversationHistory : [],
          isFollowUp,
          filters: {
            categories: selectedCategories,
            zipCode: zipCode,
            locationText: locationText,
          },
        }),
      })

      if (!response.ok) {
        throw new Error("Failed to generate referrals")
      }

      const data = await response.json()
      const endTime = Date.now()
      const duration = Math.round((endTime - startTime) / 1000)

      const newEntry = {
        prompt: prompt,
        response: data,
        timestamp: new Date().toISOString(),
      }

      setConversationHistory((prev) => [...prev, newEntry])
      setProcessingTime(`${Math.floor(duration / 60)}m ${duration % 60}s`)
      setShowResults(true)

      if (isFollowUp) {
        setFollowUpPrompt("")
      }
    } catch (error) {
      console.error("Error generating referrals:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const supportedTypes = ["application/pdf", "image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"]

      if (supportedTypes.includes(file.type)) {
        setUploadedFile(file)
        setPdfAnalysisResult("")
      } else {
        alert("Please upload a PDF or image file (PNG, JPEG, WEBP, GIF).")
      }
    }
  }

  const handleProcessFile = async () => {
    if (!uploadedFile) return

    setIsProcessingPDF(true)
    const startTime = Date.now()

    try {
      const formData = new FormData()
      formData.append("file", uploadedFile)
      formData.append(
        "filters",
        JSON.stringify({
          categories: selectedCategories,
          zipCode: zipCode,
          locationText: locationText,
        }),
      )

      const response = await fetch("/api/process-file", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error("Failed to process file")
      }

      const data = await response.json()
      const endTime = Date.now()
      const duration = Math.round((endTime - startTime) / 1000)

      setPdfAnalysisResult(data.extractedText)
      setClientDescription(data.extractedText)
      setProcessingTime(`${Math.floor(duration / 60)}m ${duration % 60}s`)

      // Automatically generate referrals after file processing
      if (data.extractedText) {
        await handleGenerateReferrals(false, data.extractedText)
      }
    } catch (error) {
      console.error("Error processing file:", error)
      alert("Error processing file. Please try again.")
    } finally {
      setIsProcessingPDF(false)
    }
  }

  const removeUploadedFile = () => {
    setUploadedFile(null)
    setPdfAnalysisResult("")
  }

  const handleStartNew = () => {
    setShowResults(false)
    setClientDescription("")
    setCaseNotes("")
    setFollowUpPrompt("")
    setConversationHistory([])
    setUploadedFile(null)
    setPdfAnalysisResult("")
    setActiveTab("text-summary")
  }

  const handleSuggestedFollowUp = (suggestion: string) => {
    handleGenerateReferrals(true, suggestion)
  }

  const buildPromptFromFilters = () => {
    let prompt = ""

    if (selectedCategories.length > 0) {
      const categoryLabels = selectedCategories
        .map((id) => resourceCategories.find((cat) => cat.id === id)?.label)
        .filter(Boolean)
      prompt += `Focus on these resource types: ${categoryLabels.join(", ")}. `
    }

    if (selectedResourceTypes.length > 0 && selectedResourceTypes.length < 3) {
      const typeLabels = selectedResourceTypes
        .map((type) => {
          switch (type) {
            case "goodwill":
              return "Goodwill internal resources"
            case "government":
              return "Government resources"
            case "community":
              return "Community resources"
            default:
              return ""
          }
        })
        .filter(Boolean)
      prompt += `Only include ${typeLabels.join(" and ")}. `
    }

    if (zipCode || locationText) {
      prompt += "Location preferences: "
      if (zipCode) {
        prompt += `(ZIP: ${zipCode})`
      }
      if (locationText) {
        prompt += `${zipCode ? ", " : ""}${locationText}`
      }
      prompt += ". "
    }

    return prompt
  }

  const triggerFileInput = () => {
    const fileInput = document.getElementById("file-upload") as HTMLInputElement
    if (fileInput) {
      fileInput.click()
    }
  }

  useEffect(() => {
    const filterPrompt = buildPromptFromFilters()

    // Extract user text by removing any existing filter prompts
    const userText = clientDescription
      .replace(/^(Focus on these resource types:.*?\. )?(Only include.*?\. )*(Location preferences:.*?\. )*/, "")
      .trim()

    // Set the description to be filter prompt + user text (or just user text if no filters)
    const newDescription = filterPrompt ? filterPrompt + userText : userText

    if (newDescription !== clientDescription) {
      setClientDescription(newDescription)
    }
  }, [selectedCategories, selectedResourceTypes, zipCode, locationText])

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Top Header */}
      <div className="bg-blue-600 text-white">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" className="text-white hover:bg-blue-700">
              <Menu className="w-5 h-5" />
            </Button>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
                <span className="text-blue-600 font-bold text-sm">CW</span>
              </div>
              <span className="font-semibold text-lg">CaseWorthy</span>
            </div>
            <div className="bg-blue-700 px-3 py-1 rounded text-sm font-medium">CASE MANAGEMENT</div>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" className="text-white hover:bg-blue-700">
              <Grid3X3 className="w-5 h-5" />
            </Button>
            <div className="flex items-center gap-2">
              <Avatar className="w-8 h-8">
                <AvatarFallback className="bg-white text-blue-600 text-sm font-semibold">RH</AvatarFallback>
              </Avatar>
              <div className="text-sm">
                <div className="font-medium">Ryan Hansz</div>
                <div className="text-blue-200 text-xs">Auditor</div>
              </div>
              <ChevronDown className="w-4 h-4 text-blue-200" />
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-1">
        {/* Left Sidebar */}
        <div className="w-64 bg-gray-800 text-white flex flex-col">
          {/* Client Info */}
          <div className="p-4 border-b border-gray-700">
            <div className="flex items-center gap-3 mb-3">
              <Avatar className="w-12 h-12">
                <AvatarFallback className="bg-blue-600 text-white">TC</AvatarFallback>
              </Avatar>
              <div>
                <h3 className="font-semibold">Test Client </h3>
                <div className="text-gray-400 text-sm flex items-center gap-1">
                  <Heart className="w-3 h-3" />
                  03/14/2000
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Client ID: 26513</span>
              <ChevronDown className="w-4 h-4 text-gray-400" />
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4">
            <div className="space-y-2">
              <Button variant="ghost" className="w-full justify-start text-white hover:bg-gray-700 gap-3">
                <Star className="w-4 h-4" />
                Favorites
              </Button>
              <Button variant="ghost" className="w-full justify-start text-white hover:bg-gray-700 gap-3">
                <Search className="w-4 h-4" />
                Find Client
              </Button>
              <Button variant="ghost" className="w-full justify-start text-white hover:bg-gray-700 gap-3">
                <UserPlus className="w-4 h-4" />
                Add Client
              </Button>
              <Button variant="ghost" className="w-full justify-start text-white hover:bg-gray-700 gap-3">
                <Settings className="w-4 h-4" />
                Case Management
              </Button>
              <Button variant="ghost" className="w-full justify-start text-white hover:bg-gray-700 gap-3">
                <ClipboardList className="w-4 h-4" />
                Assessments
              </Button>
            </div>
          </nav>

          {/* Training Environment Badge */}
          <div className="p-4">
            <div className="bg-white text-black px-3 py-2 rounded text-xs font-bold text-center">
              <div>TRAINING</div>
              <div>ENVIRONMENT</div>
              <div className="text-gray-600 font-normal mt-1">Version: 8.0.143.1</div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Content Header */}
          <div className="bg-white border-b border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Button variant="ghost" size="sm" className="text-gray-600 hover:bg-gray-100">
                  <ArrowLeft className="w-4 h-4" />
                </Button>
                <div className="text-gray-400">...</div>
                <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
              </div>
              <Button variant="outline" className="text-orange-600 border-orange-600 hover:bg-orange-50 bg-transparent">
                <MoreHorizontal className="w-4 h-4 mr-2" />
                PAGE OPTIONS
              </Button>
            </div>
          </div>

          {/* Main Content Area - Referral Tool */}
          <div className="flex-1 p-6 overflow-auto">
            <div className="border-2 border-gray-300 rounded-lg p-6 bg-white min-h-full">
              {/* Referral Tool Content */}
              <div className="max-w-4xl mx-auto">
                {showHistory ? (
                  <>
                    {/* History Header */}
                    <div className="mb-6">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-4">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowHistory(false)}
                            className="text-gray-600"
                          >
                            <ArrowLeft className="w-4 h-4 mr-2" />
                            Back to Search
                          </Button>
                          <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-gradient-to-br from-primary to-secondary rounded-xl flex items-center justify-center text-white shadow-lg">
                              <ClipboardList className="w-6 h-6" />
                            </div>
                            <div>
                              <h2 className="text-2xl font-bold text-gray-900">Search History</h2>
                              <p className="text-muted-foreground">Review your past searches and referral requests</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Search and Filter Bar */}
                    <div className="mb-6">
                      <div className="flex gap-4 items-center">
                        <div className="flex-1">
                          <Input placeholder="Search history by client name or query..." className="w-full" />
                        </div>
                        <Button variant="outline" size="sm">
                          <Filter className="w-4 h-4 mr-2" />
                          Filter
                        </Button>
                      </div>
                    </div>

                    {/* History Cards */}
                    <div className="space-y-4">
                      {mockHistory.map((item) => (
                        <Card key={item.id} className="p-6 hover:shadow-md transition-shadow cursor-pointer bg-transparent">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <h3 className="font-semibold text-lg text-gray-900">{item.clientName}</h3>
                              </div>
                              <p className="text-gray-600 mb-3">{item.searchQuery}</p>
                              <div className="flex flex-wrap gap-2 mb-3">
                                {item.resourceTypes.map((type) => (
                                  <span key={type} className="px-2 py-1 bg-muted text-muted-foreground rounded text-sm">
                                    {type}
                                  </span>
                                ))}
                              </div>
                              <div className="flex items-center gap-4 text-sm text-gray-500">
                                <span>{new Date(item.date).toLocaleDateString()}</span>
                                <span>•</span>
                                <span>{item.resultsCount} resources found</span>
                                <span>•</span>
                                <span>{item.providerTypes.join(", ")}</span>
                              </div>
                            </div>
                            <div className="flex gap-2 ml-4">
                              <Button variant="outline" size="sm">
                                <Eye className="w-4 h-4 mr-2" />
                                View
                              </Button>
                              <Button variant="outline" size="sm">
                                <RefreshCw className="w-4 h-4 mr-2" />
                                Re-run
                              </Button>
                            </div>
                          </div>
                        </Card>
                      ))}
                    </div>
                  </>
                ) : !showResults ? (
                  <>
                    {/* Header */}
                    <div className="mb-6">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl flex items-center justify-center text-white shadow-lg">
                            <Heart className="w-6 h-6" />
                          </div>
                          <div>
                            <h2 className="text-2xl font-bold text-gray-900">Find Resources </h2>
                            <p className="text-blue-600 font-medium">GenAI Referral Tool</p>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          onClick={() => setShowHistory(true)}
                          className="flex items-center gap-2"
                        >
                          <ClipboardList className="w-4 h-4" />
                          View History
                        </Button>
                      </div>
                    </div>

                    {/* Tabs */}
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
                      <TabsList className="grid w-full grid-cols-2 bg-gray-100">
                        <TabsTrigger
                          value="text-summary"
                          className="flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-blue-600"
                        >
                          <Sparkles className="w-4 h-4" />
                          Text Summary
                        </TabsTrigger>
                        <TabsTrigger
                          value="upload-forms"
                          className="flex items-center gap-2 data-[state=active]:bg-white data-[state=active]:text-blue-600"
                        >
                          <Upload className="w-4 h-4" />
                          Upload Forms
                        </TabsTrigger>
                      </TabsList>
                    </Tabs>

                    {activeTab === "text-summary" && (
                      <div className="space-y-6">
                        <Card className="bg-gray-50 border-gray-200">
                          <CardContent className="p-4 space-y-4">
                            {/* Resource Categories */}
                            <div>
                              <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                                <FileText className="w-4 h-4 text-blue-600" />
                                Focus on Specific Resource Types
                              </h4>
                              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                                {resourceCategories.map((category) => {
                                  const Icon = category.icon
                                  const isSelected = selectedCategories.includes(category.id)
                                  return (
                                    <Button
                                      key={category.id}
                                      variant={isSelected ? "default" : "outline"}
                                      size="sm"
                                      className={`text-sm flex-col justify-center px-0 h-20 ${
                                        isSelected
                                          ? "bg-blue-600 text-white hover:bg-blue-700"
                                          : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                                      }`}
                                      onClick={() => toggleCategory(category.id)}
                                    >
                                      <Icon className="mr-2 size-2.5 w-6 h-6" />
                                      {category.label}
                                    </Button>
                                  )
                                })}
                              </div>
                            </div>

                            <div>
                              <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                                <Building className="w-4 h-4 text-blue-600" />
                                Resource Provider Types
                              </h4>
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                <Button
                                  variant={selectedResourceTypes.includes("goodwill") ? "default" : "outline"}
                                  size="sm"
                                  className={`h-12 ${
                                    selectedResourceTypes.includes("goodwill")
                                      ? "bg-blue-600 text-white hover:bg-blue-700"
                                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                                  }`}
                                  onClick={() => toggleResourceType("goodwill")}
                                >
                                  <Heart className="w-4 h-4 mr-2" />
                                  Goodwill Internal
                                </Button>
                                <Button
                                  variant={selectedResourceTypes.includes("government") ? "default" : "outline"}
                                  size="sm"
                                  className={`h-12 ${
                                    selectedResourceTypes.includes("government")
                                      ? "bg-blue-600 text-white hover:bg-blue-700"
                                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                                  }`}
                                  onClick={() => toggleResourceType("government")}
                                >
                                  <Building className="w-4 h-4 mr-2" />
                                  Government
                                </Button>
                                <Button
                                  variant={selectedResourceTypes.includes("community") ? "default" : "outline"}
                                  size="sm"
                                  className={`h-12 ${
                                    selectedResourceTypes.includes("community")
                                      ? "bg-blue-600 text-white hover:bg-blue-700"
                                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                                  }`}
                                  onClick={() => toggleResourceType("community")}
                                >
                                  <Users className="w-4 h-4 mr-2" />
                                  Community
                                </Button>
                              </div>
                            </div>

                            {/* Location Filters */}
                            <div>
                              <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                                <MapPin className="w-4 h-4 text-blue-600" />
                                Location Preferences
                              </h4>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                <Input
                                  placeholder="Enter ZIP Code"
                                  value={zipCode}
                                  onChange={(e) => setZipCode(e.target.value)}
                                  className="border-gray-300 focus:ring-blue-500 focus:border-blue-500"
                                />
                                <Input
                                  placeholder="Enter location (city, area, etc.)"
                                  value={locationText}
                                  onChange={(e) => setLocationText(e.target.value)}
                                  className="border-gray-300 focus:ring-blue-500 focus:border-blue-500"
                                />
                              </div>
                            </div>

                            {/* Clear All Button */}
                            {(selectedCategories.length > 0 ||
                              selectedResourceTypes.length > 0 ||
                              zipCode ||
                              locationText) && (
                              <div className="flex justify-end">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={clearAllFilters}
                                  className="text-gray-600 hover:text-gray-800"
                                >
                                  Clear All Filters
                                </Button>
                              </div>
                            )}
                          </CardContent>
                        </Card>

                        <div className="space-y-3">
                          <label className="text-sm font-medium text-gray-900">
                            Client Description (filters automatically added above)
                          </label>
                          <Textarea
                            placeholder="The filters above will automatically be added to your prompt. Add additional details about the client's specific situation, needs, and circumstances here..."
                            value={clientDescription}
                            onChange={(e) => setClientDescription(e.target.value)}
                            className="min-h-[200px] text-base border-gray-300 focus:ring-blue-500 focus:border-blue-500"
                          />
                        </div>

                        <button
                          onClick={() => handleGenerateReferrals(false)}
                          disabled={!clientDescription.trim() || isLoading}
                          style={{
                            backgroundColor: "#2563eb",
                            color: "#ffffff",
                            padding: "12px 32px",
                            fontSize: "18px",
                            fontWeight: "500",
                            borderRadius: "6px",
                            border: "none",
                            cursor: "pointer",
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "8px",
                            boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
                            transition: "all 0.2s ease-in-out",
                          }}
                          onMouseEnter={(e) => {
                            if (!e.currentTarget.disabled) {
                              e.currentTarget.style.backgroundColor = "#1d4ed8"
                              e.currentTarget.style.boxShadow =
                                "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"
                            }
                          }}
                          onMouseLeave={(e) => {
                            if (!e.currentTarget.disabled) {
                              e.currentTarget.style.backgroundColor = "#2563eb"
                              e.currentTarget.style.boxShadow =
                                "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"
                            }
                          }}
                        >
                          <Sparkles className="w-5 h-5" />
                          {isLoading ? "Generating Resources..." : "Find Resources"}
                        </button>
                      </div>
                    )}

                    {activeTab === "upload-forms" && (
                      <div className="space-y-6">
                        <Card className="bg-gray-50 border-gray-200">
                          <CardContent className="p-6 space-y-6">
                            <div className="text-center">
                              <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
                                <Upload className="w-8 h-8 text-blue-600" />
                              </div>
                              <h3 className="text-lg font-semibold text-gray-900 mb-2">Upload Intake Form</h3>
                              <p className="text-gray-600 mb-6">
                                Upload a PDF or image of a handwritten or completed intake form. Our AI will
                                automatically extract client information and generate relevant referrals.
                              </p>
                            </div>

                            {!uploadedFile ? (
                              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
                                <input
                                  type="file"
                                  accept=".pdf,.png,.jpg,.jpeg,.webp,.gif"
                                  onChange={handleFileUpload}
                                  className="hidden"
                                  id="file-upload"
                                />
                                <div className="flex flex-col items-center">
                                  <FileText className="w-12 h-12 text-gray-400 mb-4" />
                                  <span className="text-lg font-medium text-gray-900 mb-2">Choose file to upload</span>
                                  <span className="text-gray-500 mb-4">PDF or image (PNG, JPEG, WEBP, GIF)</span>
                                  <Button
                                    type="button"
                                    onClick={triggerFileInput}
                                    className="bg-blue-600 hover:bg-blue-700"
                                  >
                                    Select File
                                  </Button>
                                </div>
                              </div>
                            ) : (
                              <div className="bg-white border border-gray-200 rounded-lg p-4">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-3">
                                    <FileText className="w-8 h-8 text-blue-600" />
                                    <div>
                                      <p className="font-medium text-gray-900">{uploadedFile.name}</p>
                                      <p className="text-sm text-gray-500">
                                        {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                                      </p>
                                    </div>
                                  </div>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={removeUploadedFile}
                                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                  >
                                    Remove
                                  </Button>
                                </div>
                              </div>
                            )}

                            {uploadedFile && (
                              <div className="space-y-4">
                                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                  <h4 className="font-medium text-blue-900 mb-2 flex items-center gap-2">
                                    <Sparkles className="w-4 h-4" />
                                    AI Processing Options
                                  </h4>
                                  <p className="text-blue-800 text-sm mb-4">
                                    The AI will extract client information from the PDF and automatically apply your
                                    selected filters below.
                                  </p>

                                  {/* Same filter options as text summary tab */}
                                  <div className="space-y-4">
                                    {/* Resource Categories */}
                                    <div>
                                      <h5 className="font-medium text-blue-900 mb-2">
                                        Focus on Specific Resource Types
                                      </h5>
                                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                                        {resourceCategories.slice(0, 6).map((category) => {
                                          const Icon = category.icon
                                          const isSelected = selectedCategories.includes(category.id)
                                          return (
                                            <Button
                                              key={category.id}
                                              variant={isSelected ? "default" : "outline"}
                                              size="sm"
                                              className={`text-xs h-12 ${
                                                isSelected
                                                  ? "bg-blue-600 text-white hover:bg-blue-700"
                                                  : "text-gray-600 hover:bg-gray-100"
                                              }`}
                                              onClick={() => toggleCategory(category.id)}
                                            >
                                              <Icon className="w-4 h-4 mr-1" />
                                              {category.label}
                                            </Button>
                                          )
                                        })}
                                      </div>
                                    </div>

                                    <div>
                                      <h5 className="font-medium text-blue-900 mb-2">Resource Provider Types</h5>
                                      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                                        <Button
                                          variant={selectedResourceTypes.includes("goodwill") ? "default" : "outline"}
                                          size="sm"
                                          className={`text-xs h-10 ${
                                            selectedResourceTypes.includes("goodwill")
                                              ? "bg-blue-600 text-white hover:bg-blue-700"
                                              : "text-gray-600 hover:bg-gray-100"
                                          }`}
                                          onClick={() => toggleResourceType("goodwill")}
                                        >
                                          <Heart className="w-3 h-3 mr-1" />
                                          Goodwill
                                        </Button>
                                        <Button
                                          variant={selectedResourceTypes.includes("government") ? "default" : "outline"}
                                          size="sm"
                                          className={`text-xs h-10 ${
                                            selectedResourceTypes.includes("government")
                                              ? "bg-blue-600 text-white hover:bg-blue-700"
                                              : "text-gray-600 hover:bg-gray-100"
                                          }`}
                                          onClick={() => toggleResourceType("government")}
                                        >
                                          <Building className="w-3 h-3 mr-1" />
                                          Government
                                        </Button>
                                        <Button
                                          variant={selectedResourceTypes.includes("community") ? "default" : "outline"}
                                          size="sm"
                                          className={`text-xs h-10 ${
                                            selectedResourceTypes.includes("community")
                                              ? "bg-blue-600 text-white hover:bg-blue-700"
                                              : "text-gray-600 hover:bg-gray-100"
                                          }`}
                                          onClick={() => toggleResourceType("community")}
                                        >
                                          <Users className="w-3 h-3 mr-1" />
                                          Community
                                        </Button>
                                      </div>
                                    </div>

                                    {/* Location Filters */}
                                    <div>
                                      <h5 className="font-medium text-blue-900 mb-2">Location Preferences</h5>
                                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                        <Input
                                          placeholder="ZIP Code"
                                          value={zipCode}
                                          onChange={(e) => setZipCode(e.target.value)}
                                          className="border-gray-300"
                                        />
                                        <Input
                                          placeholder="Location"
                                          value={locationText}
                                          onChange={(e) => setLocationText(e.target.value)}
                                          className="border-gray-300"
                                        />
                                      </div>
                                    </div>
                                  </div>
                                </div>

                                <Button
                                  onClick={handleProcessFile}
                                  disabled={isProcessingPDF}
                                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 text-lg font-medium"
                                >
                                  {isProcessingPDF ? (
                                    <>
                                      <Sparkles className="w-5 h-5 mr-2 animate-spin" />
                                      Processing File & Generating Referrals...
                                    </>
                                  ) : (
                                    <>
                                      <Sparkles className="w-5 h-5 mr-2" />
                                      Process File & Generate Referrals
                                    </>
                                  )}
                                </Button>
                              </div>
                            )}

                            {pdfAnalysisResult && (
                              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                                <h4 className="font-medium text-green-900 mb-2 flex items-center gap-2">
                                  <CheckCircle className="w-4 h-4" />
                                  PDF Processed Successfully
                                </h4>
                                <p className="text-green-800 text-sm mb-3">
                                  Client information extracted and referrals generated in {processingTime}
                                </p>
                                <div className="bg-white border border-green-200 rounded p-3 max-h-32 overflow-y-auto">
                                  <p className="text-sm text-gray-700">{pdfAnalysisResult.substring(0, 200)}...</p>
                                </div>
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      </div>
                    )}

                    {/* Empty State */}
                    {activeTab === "text-summary" && (
                      <div className="mt-12 text-center">
                        <div className="w-24 h-24 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                          <Search className="w-12 h-12 text-gray-400" />
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="space-y-6">
                    <div className="flex items-center justify-between mb-6">
                      <Button
                        onClick={handleStartNew}
                        variant="outline"
                        className="flex items-center gap-2 text-gray-600 hover:text-gray-800 hover:bg-gray-50 bg-transparent"
                      >
                        <ArrowLeft className="w-4 h-4" />
                        Back to Search
                      </Button>
                      <Button
                        onClick={handlePrintChatThread}
                        variant="outline"
                        className="flex items-center gap-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50 bg-transparent"
                      >
                        <Printer className="w-4 h-4" />
                        Print Report
                      </Button>
                    </div>

                    {conversationHistory.map((exchange, index) => (
                      <div key={index} className="space-y-4 pb-6 border-b border-gray-200 last:border-b-0">
                        {/* Question Header */}
                        <div className="bg-gray-100 rounded-2xl p-4 text-center border">
                          <h2 className="text-lg font-medium text-gray-900">{exchange.response.question}</h2>
                        </div>

                        {/* Processing Time - only show for latest */}
                        {index === conversationHistory.length - 1 && (
                          <div className="text-sm text-gray-600">Thought for {processingTime}</div>
                        )}

                        {/* Summary */}
                        <div className="text-gray-900">
                          <p className="font-medium mb-4">{exchange.response.summary}</p>
                        </div>

                        {exchange.response.resources ? (
                          <div className="space-y-6">
                            {exchange.response.resources.map((resource) => (
                              <div key={resource.number} className="space-y-3">
                                <div className="flex items-start gap-3">
                                  <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                                    {resource.number}
                                  </span>
                                  <div className="flex-1">
                                    <h3 className="font-semibold text-slate-900">
                                      {resource.title} - <span className="font-normal">{resource.service}</span>
                                    </h3>
                                    <p className="text-slate-600 mt-1">
                                      <strong>Why it fits:</strong> {resource.whyItFits}
                                    </p>
                                    <p className="text-slate-700 mt-2">
                                      <strong>Contact:</strong> {resource.contact}
                                    </p>
                                    <p className="text-slate-500 text-sm mt-1">
                                      <strong>Source:</strong> {resource.source}
                                      <a
                                        href={`https://${resource.badge}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="ml-2 text-blue-600 hover:text-blue-800 underline text-xs"
                                      >
                                        {resource.badge}
                                      </a>
                                    </p>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : exchange.response.content ? (
                          <div className="prose max-w-none text-slate-700">
                            <div
                              dangerouslySetInnerHTML={{
                                __html: parseMarkdownToHTML(exchange.response.content),
                              }}
                            />
                          </div>
                        ) : null}

                        {index === 0 &&
                          exchange.response.suggestedFollowUps &&
                          exchange.response.suggestedFollowUps.length > 0 && (
                            <div className="mt-8 p-4 bg-gray-50 rounded-lg border">
                              <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                                <MessageCircle className="w-4 h-4 text-blue-600" />
                                Suggested follow-up questions:
                              </h4>
                              <div className="space-y-2">
                                {exchange.response.suggestedFollowUps.map((suggestion, suggestionIndex) => (
                                  <Button
                                    key={suggestionIndex}
                                    variant="outline"
                                    className="text-left justify-start h-auto p-3 whitespace-normal font-medium bg-transparent"
                                    onClick={() => handleSuggestedFollowUp(suggestion)}
                                  >
                                    {suggestion}
                                  </Button>
                                ))}
                              </div>
                            </div>
                          )}
                      </div>
                    ))}

                    {/* Follow-up input */}
                    {conversationHistory.length > 0 && (
                      <div className="mt-6 p-4 border rounded-lg bg-gray-50">
                        <h4 className="font-medium text-gray-900 mb-3">Ask a follow-up question:</h4>
                        <div className="space-y-3">
                          <Textarea
                            placeholder="Ask for more specific information, clarify details, or request additional resources..."
                            value={followUpPrompt}
                            onChange={(e) => setFollowUpPrompt(e.target.value)}
                            className="min-h-[80px] border-gray-300 focus:ring-blue-500 focus:border-blue-500"
                          />
                          <Button
                            onClick={() => handleGenerateReferrals(true)}
                            disabled={!followUpPrompt.trim() || isLoading}
                            className="bg-blue-600 hover:bg-blue-700"
                          >
                            <MessageCircle className="w-4 h-4 mr-2" />
                            {isLoading ? "Generating..." : "Ask Follow-up"}
                          </Button>
                        </div>
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex items-center gap-3 pt-6 border-t border-gray-200">
                      <Button variant="ghost" size="sm" className="hover:bg-gray-100">
                        <Copy className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm" className="hover:bg-gray-100" onClick={handlePrintChatThread}>
                        <Printer className="w-4 h-4 mr-2" />
                        Print Report
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setShowResults(false)
                          setConversationHistory([])
                          setClientDescription("")
                          setFollowUpPrompt("")
                        }}
                        className="text-blue-600 hover:bg-blue-50 bg-transparent"
                      >
                        <RotateCcw className="w-4 h-4 mr-2" />
                        Start New Case
                      </Button>
                    </div>

                    <div className="flex justify-center pt-4">
                      <Button
                        onClick={handleStartNew}
                        variant="outline"
                        className="text-blue-600 hover:bg-blue-50 border-blue-200 bg-transparent"
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        Start New Session
                      </Button>
                    </div>

                    {/* Staff Actions */}
                    <Card className="bg-gray-50 mt-6">
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-gray-900">
                          <CheckCircle className="w-5 h-5 text-blue-600" />
                          Staff Actions
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex flex-wrap gap-3 mb-4">
                          <Button className="bg-blue-600 hover:bg-blue-700 shadow-sm">
                            <CheckCircle className="w-4 h-4 mr-2" />
                            Approve Referrals
                          </Button>
                          <Button variant="outline" className="text-blue-600 hover:bg-blue-50 bg-transparent">
                            <Printer className="w-4 h-4 mr-2" />
                            Print for Client
                          </Button>
                          <Button variant="outline" className="text-blue-600 hover:bg-blue-50 bg-transparent">
                            <FileText className="w-4 h-4 mr-2" />
                            Add to Case Notes
                          </Button>
                        </div>

                        <div>
                          <h4 className="font-medium mb-2 text-gray-900">Case Notes:</h4>
                          <Textarea
                            placeholder="Add notes about client interaction or follow-up actions..."
                            value={caseNotes}
                            onChange={(e) => setCaseNotes(e.target.value)}
                            className="min-h-[80px] border-gray-300 focus:ring-blue-500 focus:border-blue-500"
                          />
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
