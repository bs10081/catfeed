import NextAuth from "next-auth"

declare module "next-auth" {
  interface User {
    username: string
    forcePasswordChange: boolean
  }

  interface Session {
    user: User & {
      username: string
      forcePasswordChange: boolean
    }
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    username: string
    forcePasswordChange: boolean
  }
} 