import { PrismaAdapter } from "@auth/prisma-adapter"
import { NextAuthOptions } from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"
import { compare } from "bcryptjs"
import { prisma } from "./prisma"

export const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(prisma),
  session: {
    strategy: "jwt",
  },
  pages: {
    signIn: "/login",
  },
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.username || !credentials?.password) {
          throw new Error("請輸入使用者名稱和密碼")
        }

        const user = await prisma.admin.findUnique({
          where: {
            username: credentials.username,
          },
        })

        if (!user) {
          throw new Error("使用者名稱或密碼錯誤")
        }

        if (user.accountLockedUntil && user.accountLockedUntil > new Date()) {
          throw new Error("帳號已被鎖定，請稍後再試")
        }

        const isPasswordValid = await compare(credentials.password, user.passwordHash)

        if (!isPasswordValid) {
          // 更新失敗登入次數
          const failedAttempts = (user.failedLoginAttempts || 0) + 1
          const updates: any = {
            failedLoginAttempts: failedAttempts,
            lastFailedLogin: new Date(),
          }

          // 如果失敗次數達到 5 次，鎖定帳號 30 分鐘
          if (failedAttempts >= 5) {
            updates.accountLockedUntil = new Date(Date.now() + 30 * 60 * 1000)
          }

          await prisma.admin.update({
            where: { id: user.id },
            data: updates,
          })

          throw new Error("使用者名稱或密碼錯誤")
        }

        // 重置失敗登入次數
        await prisma.admin.update({
          where: { id: user.id },
          data: {
            failedLoginAttempts: 0,
            lastFailedLogin: null,
            accountLockedUntil: null,
          },
        })

        return {
          id: user.id.toString(),
          username: user.username,
          forcePasswordChange: user.forcePasswordChange,
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        return {
          ...token,
          username: user.username,
          forcePasswordChange: user.forcePasswordChange,
        }
      }
      return token
    },
    async session({ session, token }) {
      return {
        ...session,
        user: {
          ...session.user,
          username: token.username,
          forcePasswordChange: token.forcePasswordChange,
        },
      }
    },
  },
} 