/**
 * Relate (LuxStore) - Node.js Email Microservice using Nodemailer
 * Called securely by the Flask backend for dispatching OTP verification emails.
 */

require('dotenv').config();
const nodemailer = require('nodemailer');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
if (args.length < 2) {
    console.error(JSON.stringify({
        success: false,
        error: "Usage: node email_service.js <to_email> <otp_code> [user_name]"
    }));
    process.exit(1);
}

const toEmail = args[0].trim();
const otpCode = args[1].trim();
const userName = (args[2] || "Valued Customer").trim();

const smtpHost = process.env.SMTP_HOST || "";
const smtpPort = parseInt(process.env.SMTP_PORT || "587", 10);
const smtpSecure = process.env.SMTP_SECURE === "true" || smtpPort === 465;
const smtpUser = process.env.SMTP_USER || "";
const smtpPass = process.env.SMTP_PASS || "";
const fromEmail = process.env.EMAIL_FROM || '"Relate LuxStore" <no-reply@luxstore.com>';

const htmlTemplate = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Relate LuxStore Password Reset Code</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0b0f19; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f3f4f6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0b0f19; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="100%" max-width="560px" style="max-width: 560px; background: #161b26; border-radius: 16px; border: 1px solid #232936; box-shadow: 0 20px 40px rgba(0,0,0,0.5); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 36px 40px 24px; text-align: center; background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%); border-bottom: 1px solid #232936;">
                            <h1 style="margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px; color: #ffffff;">
                                <span style="background: linear-gradient(135deg, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Relate</span> <span style="font-weight: 300; color: #94a3b8;">LuxStore</span>
                            </h1>
                            <p style="margin: 6px 0 0; color: #94a3b8; font-size: 13px; letter-spacing: 1px; text-transform: uppercase;">Security Verification</p>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 36px 40px;">
                            <p style="margin: 0 0 16px; font-size: 16px; color: #e2e8f0;">Hello <strong>${userName}</strong>,</p>
                            <p style="margin: 0 0 24px; font-size: 15px; color: #94a3b8; line-height: 1.6;">
                                We received a request to reset your password for your Relate LuxStore account. Use the verification code below to complete the reset process:
                            </p>
                            
                            <!-- OTP Box -->
                            <div style="background: #0f131c; border: 2px dashed #6366f1; border-radius: 12px; padding: 24px; text-align: center; margin: 28px 0;">
                                <span style="font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #a5b4fc; font-family: 'Courier New', Courier, monospace;">${otpCode}</span>
                                <p style="margin: 8px 0 0; font-size: 12px; color: #f59e0b; font-weight: 500;">
                                    ⏱️ Code expires in <strong>5 minutes</strong>
                                </p>
                            </div>
                            
                            <p style="margin: 0 0 16px; font-size: 14px; color: #94a3b8; line-height: 1.5;">
                                If you did not request a password reset, you can safely disregard this email. Your password will remain unchanged and your account remains secure.
                            </p>
                            
                            <div style="margin-top: 32px; padding-top: 20px; border-top: 1px solid #232936; font-size: 12px; color: #64748b; line-height: 1.5;">
                                <p style="margin: 0;">This is an automated security transmission. Please do not reply directly to this email.</p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; background: #0f131c; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #1e2430;">
                            © 2026 Relate (LuxStore) Recommendation Engine. All rights reserved.
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
`;

async function sendMail() {
    // If SMTP credentials are configured and valid
    if (smtpHost && smtpUser && smtpPass && smtpPass !== "your_app_specific_password") {
        try {
            const transporter = nodemailer.createTransport({
                host: smtpHost,
                port: smtpPort,
                secure: smtpSecure,
                auth: {
                    user: smtpUser,
                    pass: smtpPass
                }
            });

            const info = await transporter.sendMail({
                from: fromEmail,
                to: toEmail,
                subject: `Your Relate LuxStore Password Reset Code: ${otpCode}`,
                text: `Hello ${userName},\n\nYour password reset code is: ${otpCode}\n\nThis code expires in 5 minutes. If you did not request this, please ignore this email.`,
                html: htmlTemplate
            });

            console.log(JSON.stringify({
                success: true,
                mode: "smtp",
                messageId: info.messageId,
                to: toEmail
            }));
            process.exit(0);
        } catch (err) {
            console.error(JSON.stringify({
                success: false,
                error: err.message,
                mode: "smtp_failed"
            }));
            // Fall through to dev log fallback so developer/tester is not blocked
        }
    }

    // Development / Local Fallback Mode: Log to logs/otp_dev_log.json
    try {
        const logsDir = path.join(__dirname, 'logs');
        if (!fs.existsSync(logsDir)) {
            fs.mkdirSync(logsDir, { recursive: true });
        }
        const logPath = path.join(logsDir, 'otp_dev_log.json');
        let logs = [];
        if (fs.existsSync(logPath)) {
            try {
                logs = JSON.parse(fs.readFileSync(logPath, 'utf8'));
            } catch (e) {
                logs = [];
            }
        }
        logs.unshift({
            timestamp: new Date().toISOString(),
            to: toEmail,
            name: userName,
            otp: otpCode,
            status: "simulated_dispatch"
        });
        if (logs.length > 50) logs = logs.slice(0, 50);
        fs.writeFileSync(logPath, JSON.stringify(logs, null, 2));

        console.log(JSON.stringify({
            success: true,
            mode: "dev_simulation",
            to: toEmail,
            otp: otpCode,
            note: "SMTP not configured or failed; OTP logged to otp_dev_log.json"
        }));
        process.exit(0);
    } catch (logErr) {
        console.error(JSON.stringify({
            success: false,
            error: logErr.message
        }));
        process.exit(1);
    }
}

sendMail();

