//
//  Copyright (c) 2021 Open Whisper Systems. All rights reserved.
//

NS_ASSUME_NONNULL_BEGIN

@class MessageBody;
@class MessageSender;
@class OWSContact;
@class OWSLinkPreviewDraft;
@class OWSQuotedReplyModel;
@class SDSAnyReadTransaction;
@class SDSAnyWriteTransaction;
@class SignalAttachment;
@class SignalServiceAddress;
@class StickerInfo;
@class StickerMetadata;
@class TSContactThread;
@class TSGroupThread;
@class TSInteraction;
@class TSOutgoingMessage;
@class TSThread;

#pragma mark -

@interface ThreadUtil : NSObject

#pragma mark - Durable Message Enqueue

+ (TSOutgoingMessage *)enqueueMessageWithBody:(MessageBody *)messageBody
                                       thread:(TSThread *)thread
                             quotedReplyModel:(nullable OWSQuotedReplyModel *)quotedReplyModel
                             linkPreviewDraft:(nullable nullable OWSLinkPreviewDraft *)linkPreviewDraft
                                  transaction:(SDSAnyReadTransaction *)transaction;

+ (TSOutgoingMessage *)enqueueMessageWithBody:(nullable MessageBody *)messageBody
                             mediaAttachments:(NSArray<SignalAttachment *> *)attachments
                                       thread:(TSThread *)thread
                             quotedReplyModel:(nullable OWSQuotedReplyModel *)quotedReplyModel
                             linkPreviewDraft:(nullable nullable OWSLinkPreviewDraft *)linkPreviewDraft
                                  transaction:(SDSAnyReadTransaction *)transaction;

+ (nullable TSOutgoingMessage *)createUnsentMessageWithBody:(nullable MessageBody *)messageBody
                                           mediaAttachments:(NSArray<SignalAttachment *> *)mediaAttachments
                                                     thread:(TSThread *)thread
                                           quotedReplyModel:(nullable OWSQuotedReplyModel *)quotedReplyModel
                                           linkPreviewDraft:(nullable nullable OWSLinkPreviewDraft *)linkPreviewDraft
                                                transaction:(SDSAnyWriteTransaction *)transaction
                                                      error:(NSError **)error;

+ (TSOutgoingMessage *)enqueueMessageWithInstalledSticker:(StickerInfo *)stickerInfo thread:(TSThread *)thread;

+ (TSOutgoingMessage *)enqueueMessageWithUninstalledSticker:(StickerMetadata *)stickerMetadata
                                                stickerData:(NSData *)stickerData
                                                     thread:(TSThread *)thread;

#pragma mark - Profile Whitelist

// This method should be called right _before_ we send a message to a thread,
// since we want to auto-add any thread to the profile whitelist that was
// initiated by the local user OR if there was a pending message request and
// the local user took an action like initiating a call or updating the DM timer.
//
// Returns YES IFF the thread was just added to the profile whitelist.
+ (BOOL)addThreadToProfileWhitelistIfEmptyOrPendingRequestAndSetDefaultTimerWithSneakyTransaction:(TSThread *)thread
    NS_SWIFT_NAME(addThreadToProfileWhitelistIfEmptyOrPendingRequestAndSetDefaultTimerWithSneakyTransaction(thread:));
+ (BOOL)addThreadToProfileWhitelistIfEmptyOrPendingRequestAndSetDefaultTimer:(TSThread *)thread
                                                                 transaction:(SDSAnyWriteTransaction *)transaction
    NS_SWIFT_NAME(addThreadToProfileWhitelistIfEmptyOrPendingRequestAndSetDefaultTimer(thread:transaction:));

#pragma mark - Delete Content

+ (void)deleteAllContent;

@end

NS_ASSUME_NONNULL_END
