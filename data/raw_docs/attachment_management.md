# Attachment Management Module

The attachment management module handles file uploads and document attachments.

## APIs

- `uploadAttachment` - Uploads a file attachment.
- `downloadAttachment` - Downloads an attached file.
- `deleteAttachment` - Deletes an attachment.

## Error Codes

- `ATT_001` - File size exceeds limit. Solved by compressing file or using smaller file.
- `ATT_002` - Unsupported file format. Solved by converting to supported format.
- `ATT_003` - Upload timeout. Solved by checking network connection.

## Roles

- System User - Requires ATTACHMENT_UPLOAD permission.
- Administrator - Requires ATTACHMENT_DELETE permission.
