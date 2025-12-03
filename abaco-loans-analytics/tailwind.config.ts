import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // ABACO Color System
      colors: {
        abaco: {
          primary: {
            light: "#C1A6FF",
            DEFAULT: "#A855F7",
            medium: "#A855F7",
            dark: "#5F4896",
            darker: "#4C3B78",
          },
          background: {
            primary: "#030E19",
            secondary: "#0F172A",
            tertiary: "#1E293B",
            glass: "rgba(15, 23, 42, 0.6)",
            overlay: "rgba(168, 85, 247, 0.1)",
          },
          text: {
            primary: "#FFFFFF",
            secondary: "#C1A6FF",
            muted: "#94A3B8",
            accent: "#A855F7",
          },
          border: {
            primary: "rgba(168, 85, 247, 0.2)",
            secondary: "rgba(193, 166, 255, 0.1)",
            accent: "rgba(168, 85, 247, 0.4)",
          },
          status: {
            success: "#10B981",
            warning: "#F59E0B",
            error: "#EF4444",
            info: "#3B82F6",
          },
          financial: {
            growth: "#10B981",
            risk: "#EF4444",
            neutral: "#6B7280",
            premium: "#F59E0B",
          },
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--brand-primary-medium))",
          foreground: "hsl(var(--foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },

      // ABACO Typography
      fontFamily: {
        lato: ["Lato", "sans-serif"],
        poppins: ["Poppins", "sans-serif"],
        sans: ["Lato", "sans-serif"],
      },

      // 4K Optimized Spacing
      spacing: {
        "18": "4.5rem",
        "88": "22rem",
        "128": "32rem",
        "144": "36rem",
      },

      // Enhanced Shadows for Glass Morphism
      boxShadow: {
        "abaco-sm": "0 1px 2px 0 rgba(168, 85, 247, 0.05)",
        "abaco-md": "0 4px 6px -1px rgba(168, 85, 247, 0.1)",
        "abaco-lg": "0 10px 15px -3px rgba(168, 85, 247, 0.1)",
        "abaco-xl": "0 20px 25px -5px rgba(168, 85, 247, 0.15)",
        "abaco-glow": "0 0 20px rgba(168, 85, 247, 0.3)",
        "abaco-inner": "inset 0 2px 4px 0 rgba(168, 85, 247, 0.1)",
      },

      // ABACO Gradient Backgrounds
      backgroundImage: {
        "abaco-primary":
          "linear-gradient(135deg, #C1A6FF 0%, #A855F7 50%, #5F4896 100%)",
        "abaco-secondary":
          "linear-gradient(135deg, #030E19 0%, #1E293B 50%, #030E19 100%)",
        "abaco-glass":
          "linear-gradient(135deg, rgba(15, 23, 42, 0.4) 0%, rgba(30, 41, 59, 0.2) 100%)",
        "abaco-glow":
          "radial-gradient(ellipse at center, rgba(168, 85, 247, 0.15) 0%, transparent 70%)",
      },

      // Border Radius for Modern Design
      borderRadius: {
        "abaco-sm": "0.25rem",
        "abaco-md": "0.5rem",
        "abaco-lg": "0.75rem",
        "abaco-xl": "1rem",
        "abaco-2xl": "1.5rem",
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },

      // Animation Curves
      transitionTimingFunction: {
        abaco: "cubic-bezier(0.4, 0, 0.2, 1)",
        "abaco-bounce": "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
      },

      // Custom Animations
      animation: {
        "abaco-pulse": "abaco-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "abaco-glow": "abaco-glow 3s ease-in-out infinite alternate",
        "abaco-float": "abaco-float 6s ease-in-out infinite",
      },

      // Keyframes
      keyframes: {
        "abaco-pulse": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        "abaco-glow": {
          "0%": { boxShadow: "0 0 20px rgba(168, 85, 247, 0.3)" },
          "100%": { boxShadow: "0 0 40px rgba(168, 85, 247, 0.6)" },
        },
        "abaco-float": {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
      },

      // Backdrop Blur
      backdropBlur: {
        abaco: "12px",
        "abaco-lg": "16px",
      },

      // Screen Sizes for 4K Support
      screens: {
        "3xl": "1920px",
        "4xl": "2560px",
        "5xl": "3840px",
      },
    },
  },
  plugins: [],
};

export default config;
